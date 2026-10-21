import { useEffect, useState } from 'react'

export default function TrustGauge({ score, size = 160 }) {
  const [animated, setAnimated] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(score), 100)
    return () => clearTimeout(t)
  }, [score])

  const color = score >= 70 ? '#10b981' : score >= 45 ? '#f59e0b' : '#ef4444'
  const glowColor = score >= 70 ? 'rgba(16,185,129,0.3)' : score >= 45 ? 'rgba(245,158,11,0.3)' : 'rgba(239,68,68,0.3)'
  const label = score >= 70 ? 'Low Risk' : score >= 45 ? 'Medium Risk' : 'High Risk'

  const r = size * 0.38
  const cx = size / 2
  const cy = size / 2
  const circ = 2 * Math.PI * r
  const dash = (animated / 100) * circ

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ filter: `drop-shadow(0 0 12px ${glowColor})` }}>
        <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {/* Track */}
          <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(59,130,246,0.08)" strokeWidth="10" />
          {/* Progress */}
          <circle
            cx={cx} cy={cy} r={r} fill="none"
            stroke={color} strokeWidth="10"
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
            transform={`rotate(-90 ${cx} ${cy})`}
            style={{ transition: 'stroke-dasharray 1.4s cubic-bezier(0.4,0,0.2,1)' }}
          />
          {/* Score */}
          <text x={cx} y={cy - 6} textAnchor="middle" fill="white" fontSize={size * 0.175} fontWeight="800" fontFamily="Inter,sans-serif">{score}</text>
          <text x={cx} y={cy + 12} textAnchor="middle" fill="#475569" fontSize={size * 0.075} fontFamily="Inter,sans-serif">/ 100</text>
        </svg>
      </div>
      <span className="text-xs font-semibold px-3 py-1 rounded-full" style={{ background: `${color}18`, color, border: `1px solid ${color}30` }}>
        {label}
      </span>
    </div>
  )
}
