const CONFIG = {
  low:     { bg: 'rgba(16,185,129,0.12)',  color: '#34d399', border: 'rgba(16,185,129,0.2)',  dot: '#10b981', label: 'Low Risk' },
  medium:  { bg: 'rgba(245,158,11,0.12)',  color: '#fbbf24', border: 'rgba(245,158,11,0.2)',  dot: '#f59e0b', label: 'Medium Risk' },
  high:    { bg: 'rgba(239,68,68,0.12)',   color: '#f87171', border: 'rgba(239,68,68,0.2)',   dot: '#ef4444', label: 'High Risk' },
  unknown: { bg: 'rgba(100,116,139,0.12)', color: '#94a3b8', border: 'rgba(100,116,139,0.2)', dot: '#64748b', label: 'Unknown' },
}

export default function RiskBadge({ level, size = 'sm' }) {
  const c = CONFIG[level] || CONFIG.unknown
  const pad = size === 'lg' ? 'px-3 py-1.5 text-xs' : 'px-2 py-0.5 text-[11px]'
  return (
    <span className={`inline-flex items-center gap-1.5 font-semibold rounded-full ${pad}`} style={{ background: c.bg, color: c.color, border: `1px solid ${c.border}` }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: c.dot }} />
      {c.label}
    </span>
  )
}
