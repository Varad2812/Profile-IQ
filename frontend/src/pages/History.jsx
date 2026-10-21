import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Calendar, ArrowRight, Filter } from 'lucide-react'
import RiskBadge from '../components/ui/RiskBadge'
import api from '../lib/api'

const FILTERS = ['all', 'low', 'medium', 'high']

export default function History() {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/history').then(({ data }) => setHistory(data)).finally(() => setLoading(false))
  }, [])

  const filtered = history.filter(a =>
    (filter === 'all' || a.risk_level === filter) &&
    a.profile_url.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-5xl space-y-4">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by URL..." className="input-field pl-9 py-2 text-xs" />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter size={13} className="text-slate-600" />
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)} className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize ${filter === f ? 'text-white' : 'text-slate-500 hover:text-slate-300'}`} style={filter === f ? { background: 'rgba(59,130,246,0.2)', border: '1px solid rgba(59,130,246,0.3)' } : { background: 'rgba(59,130,246,0.05)', border: '1px solid rgba(59,130,246,0.1)' }}>
              {f}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-600">{filtered.length} records</span>
      </div>

      {/* Table */}
      <div className="glass overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(59,130,246,0.08)' }}>
              {['Profile URL', 'Trust Score', 'Confidence', 'Risk Level', 'Date', ''].map(h => (
                <th key={h} className="text-left px-4 py-3 text-[11px] font-semibold text-slate-600 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? Array(6).fill(0).map((_, i) => (
              <tr key={i}>{Array(6).fill(0).map((_, j) => <td key={j} className="px-4 py-3"><div className="h-4 skeleton" /></td>)}</tr>
            )) : filtered.length === 0 ? (
              <tr><td colSpan={6} className="text-center py-14 text-slate-600 text-sm">No analyses found</td></tr>
            ) : filtered.map(a => (
              <tr key={a.id} className="hover:bg-blue-500/[0.03] transition-colors cursor-pointer group" style={{ borderBottom: '1px solid rgba(59,130,246,0.05)' }} onClick={() => navigate(`/analysis/${a.id}`)}>
                <td className="px-4 py-3">
                  <p className="text-slate-300 text-xs truncate max-w-xs">{a.profile_url}</p>
                </td>
                <td className="px-4 py-3">
                  <span className="font-bold text-sm" style={{ color: a.trust_score >= 70 ? '#10b981' : a.trust_score >= 45 ? '#f59e0b' : '#ef4444' }}>{a.trust_score}%</span>
                </td>
                <td className="px-4 py-3 text-xs text-slate-500">{a.confidence ?? '—'}%</td>
                <td className="px-4 py-3"><RiskBadge level={a.risk_level} /></td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-600">
                    <Calendar size={11} /> {new Date(a.created_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <ArrowRight size={13} className="text-slate-700 group-hover:text-blue-400 transition-colors" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
