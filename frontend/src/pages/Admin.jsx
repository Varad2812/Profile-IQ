import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Users, BarChart3, ShieldAlert, TrendingUp, Shield, Download, Search } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { StatCard, SkeletonCard } from '../components/ui/StatCard'
import RiskBadge from '../components/ui/RiskBadge'
import api from '../lib/api'

function exportCSV(analyses) {
  const rows = [['ID','User ID','Profile URL','Trust Score','Confidence','Risk Level','Date']]
  analyses.forEach(a => rows.push([a.id, a.user_id, a.profile_url, a.trust_score, a.confidence ?? '', a.risk_level, new Date(a.created_at).toLocaleString()]))
  const csv = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = 'profileiq_analyses.csv'; a.click()
  URL.revokeObjectURL(url)
}

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    Promise.all([api.get('/admin/stats'), api.get('/admin/users'), api.get('/admin/analyses')])
      .then(([s, u, a]) => { setStats(s.data); setUsers(u.data); setAnalyses(a.data) })
      .finally(() => setLoading(false))
  }, [])

  const barData = stats ? [
    { name: 'Low',    value: stats.low_risk_count,    color: '#10b981' },
    { name: 'Medium', value: stats.medium_risk_count, color: '#f59e0b' },
    { name: 'High',   value: stats.high_risk_count,   color: '#ef4444' },
  ] : []

  const filtered = analyses.filter(a => a.profile_url.toLowerCase().includes(search.toLowerCase()))

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-6xl space-y-5">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.2)' }}>
          <Shield size={15} className="text-purple-400" />
        </div>
        <div>
          <p className="text-sm font-bold text-white">Admin Panel</p>
          <p className="text-xs text-slate-600">System management and analytics</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading || !stats ? Array(4).fill(0).map((_, i) => <SkeletonCard key={i} />) : (
          <>
            <StatCard index={0} label="Total Users"        value={stats.total_users}       icon={Users}       color="#8b5cf6" />
            <StatCard index={1} label="Total Analyses"     value={stats.total_analyses}    icon={BarChart3}   color="#3b82f6" />
            <StatCard index={2} label="Avg Trust Score"    value={`${stats.avg_trust_score}%`} icon={TrendingUp} color="#10b981" />
            <StatCard index={3} label="High Risk Profiles" value={stats.high_risk_count}   icon={ShieldAlert} color="#ef4444" />
          </>
        )}
      </div>

      {/* Charts + Users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="glass p-5">
          <p className="text-sm font-semibold text-white mb-4">Risk Distribution</p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={barData} barSize={44}>
              <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip contentStyle={{ background: '#0a1a35', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, color: '#e2e8f0', fontSize: 11 }} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {barData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-5">
          <p className="text-sm font-semibold text-white mb-4">Registered Users ({users.length})</p>
          <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
            {loading ? Array(4).fill(0).map((_, i) => <div key={i} className="h-10 skeleton" />) :
              users.map(u => (
                <div key={u.id} className="flex items-center justify-between p-2.5 rounded-xl" style={{ background: 'rgba(59,130,246,0.04)', border: '1px solid rgba(59,130,246,0.08)' }}>
                  <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold text-white" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)' }}>
                      {u.email[0].toUpperCase()}
                    </div>
                    <p className="text-xs text-slate-300 truncate max-w-[160px]">{u.email}</p>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: u.role === 'admin' ? 'rgba(139,92,246,0.2)' : 'rgba(59,130,246,0.15)', color: u.role === 'admin' ? '#a78bfa' : '#60a5fa' }}>
                    {u.role}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Analyses table */}
      <div className="glass overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'rgba(59,130,246,0.08)' }}>
          <p className="text-sm font-semibold text-white">All Analyses</p>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-600" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search URL..." className="input-field pl-7 py-1.5 text-xs w-48" />
            </div>
            <button onClick={() => exportCSV(analyses)} className="btn-ghost text-xs py-1.5 px-3">
              <Download size={12} /> Export CSV
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(59,130,246,0.08)' }}>
                {['ID','User','Profile URL','Trust','Confidence','Risk','Date'].map(h => (
                  <th key={h} className="text-left px-4 py-2.5 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? Array(5).fill(0).map((_, i) => (
                <tr key={i}>{Array(7).fill(0).map((_, j) => <td key={j} className="px-4 py-2.5"><div className="h-4 skeleton" /></td>)}</tr>
              )) : filtered.map(a => (
                <tr key={a.id} className="hover:bg-blue-500/[0.03] transition-colors" style={{ borderBottom: '1px solid rgba(59,130,246,0.04)' }}>
                  <td className="px-4 py-2.5 text-xs text-slate-600">#{a.id}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{a.user_id}</td>
                  <td className="px-4 py-2.5 text-xs text-slate-300 max-w-[200px] truncate">{a.profile_url}</td>
                  <td className="px-4 py-2.5 text-sm font-bold" style={{ color: a.trust_score >= 70 ? '#10b981' : a.trust_score >= 45 ? '#f59e0b' : '#ef4444' }}>{a.trust_score}%</td>
                  <td className="px-4 py-2.5 text-xs text-slate-500">{a.confidence ?? '—'}%</td>
                  <td className="px-4 py-2.5"><RiskBadge level={a.risk_level} /></td>
                  <td className="px-4 py-2.5 text-xs text-slate-600">{new Date(a.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.div>
  )
}
