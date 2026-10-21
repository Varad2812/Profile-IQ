import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { BarChart3, ShieldAlert, TrendingUp, Users, Search, ArrowRight, Clock } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { StatCard, SkeletonCard } from '../components/ui/StatCard'
import RiskBadge from '../components/ui/RiskBadge'
import api from '../lib/api'

const WEEK = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
const PIE_COLORS = ['#10b981','#f59e0b','#ef4444']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-sm px-3 py-2 text-xs">
      <p className="text-slate-400">{label}</p>
      <p className="text-white font-semibold">{payload[0].value} analyses</p>
    </div>
  )
}

export default function Dashboard() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/history').then(({ data }) => setHistory(data)).finally(() => setLoading(false))
  }, [])

  const avg = history.length ? Math.round(history.reduce((s, a) => s + a.trust_score, 0) / history.length) : 0
  const high = history.filter(a => a.risk_level === 'high').length
  const pieData = [
    { name: 'Low',    value: history.filter(a => a.risk_level === 'low').length || 0 },
    { name: 'Medium', value: history.filter(a => a.risk_level === 'medium').length || 0 },
    { name: 'High',   value: high || 0 },
  ]
  const trendData = WEEK.map((day, i) => ({ day, analyses: history.filter(a => new Date(a.created_at).getDay() === (i + 1) % 7).length }))

  return (
    <div className="space-y-5 max-w-6xl">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {loading ? Array(4).fill(0).map((_, i) => <SkeletonCard key={i} />) : (
          <>
            <StatCard index={0} label="Total Analyses"   value={history.length} icon={BarChart3}   color="#3b82f6" />
            <StatCard index={1} label="Avg Trust Score"  value={`${avg}%`}      icon={TrendingUp}  color="#6366f1" sub={avg >= 70 ? 'Healthy' : avg >= 45 ? 'Moderate' : 'At Risk'} />
            <StatCard index={2} label="High Risk Found"  value={high}           icon={ShieldAlert} color="#ef4444" />
            <StatCard index={3} label="Profiles Checked" value={history.length} icon={Users}       color="#10b981" sub="All time" />
          </>
        )}
      </div>

      {/* Quick action */}
      <div className="glass p-5 flex items-center justify-between" style={{ background: 'linear-gradient(135deg,rgba(59,130,246,0.08),rgba(99,102,241,0.08))', borderColor: 'rgba(59,130,246,0.2)' }}>
        <div>
          <p className="font-semibold text-white text-sm">Analyze a new profile</p>
          <p className="text-xs text-slate-500 mt-0.5">Paste an Instagram URL and get results in seconds</p>
        </div>
        <button onClick={() => navigate('/analyze')} className="btn-primary shrink-0">
          <Search size={14} /> Analyze Now <ArrowRight size={14} />
        </button>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="glass p-5 lg:col-span-2">
          <p className="text-sm font-semibold text-white mb-4">Analysis Activity</p>
          <ResponsiveContainer width="100%" height={170}>
            <AreaChart data={trendData}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#3b82f6" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="day" tick={{ fill: '#334155', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#334155', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="analyses" stroke="#3b82f6" fill="url(#areaGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-5">
          <p className="text-sm font-semibold text-white mb-4">Risk Distribution</p>
          {history.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-slate-600 text-xs">No data yet</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={130}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={38} outerRadius={58} paddingAngle={3} dataKey="value">
                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#0a1a35', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, color: '#e2e8f0', fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-4 mt-2">
                {pieData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-1.5 text-xs text-slate-500">
                    <span className="w-2 h-2 rounded-full" style={{ background: PIE_COLORS[i] }} />
                    {d.name} ({d.value})
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Recent */}
      <div className="glass p-5">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-white">Recent Analyses</p>
          <button onClick={() => navigate('/history')} className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
            View all <ArrowRight size={11} />
          </button>
        </div>
        {loading ? (
          <div className="space-y-2">{Array(3).fill(0).map((_, i) => <div key={i} className="h-12 skeleton" />)}</div>
        ) : history.length === 0 ? (
          <div className="text-center py-10">
            <Search size={28} className="text-slate-700 mx-auto mb-2" />
            <p className="text-slate-500 text-sm">No analyses yet</p>
            <button onClick={() => navigate('/analyze')} className="btn-primary mt-3 text-xs px-4 py-2">Run First Analysis</button>
          </div>
        ) : (
          <div className="space-y-1.5">
            {history.slice(0, 6).map(a => (
              <div key={a.id} onClick={() => navigate(`/analysis/${a.id}`)} className="flex items-center justify-between p-3 rounded-xl cursor-pointer hover:bg-blue-500/5 transition-colors group" style={{ border: '1px solid rgba(59,130,246,0.06)' }}>
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0" style={{ background: 'rgba(59,130,246,0.1)' }}>
                    <Search size={12} className="text-blue-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm text-slate-300 truncate max-w-xs">{a.profile_url}</p>
                    <div className="flex items-center gap-1 text-xs text-slate-600 mt-0.5">
                      <Clock size={10} /> {new Date(a.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-sm font-bold" style={{ color: a.trust_score >= 70 ? '#10b981' : a.trust_score >= 45 ? '#f59e0b' : '#ef4444' }}>{a.trust_score}%</span>
                  <RiskBadge level={a.risk_level} />
                  <ArrowRight size={13} className="text-slate-700 group-hover:text-slate-400 transition-colors" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
