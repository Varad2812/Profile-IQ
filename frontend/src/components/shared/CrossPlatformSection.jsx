import { Globe, CheckCircle, AlertTriangle, Users } from 'lucide-react'
import { PLATFORM_STYLES } from './OcrDataSection'

export default function CrossPlatformSection({ ms }) {
  if (!ms || !ms.identity_platforms) return null
  const platforms = typeof ms.identity_platforms === 'string' ? ms.identity_platforms.split(',').filter(Boolean) : []
  const riskFlags = typeof ms.identity_risk_flags === 'string' ? ms.identity_risk_flags.split(',').filter(Boolean) : []
  const hasFaceMatch = ms.identity_face_matches > 0

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Globe size={15} className="text-blue-400" />
          <p className="text-xs font-semibold text-white uppercase tracking-wider">Cross-Platform Verification</p>
          <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase"
            style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa' }}>OSINT</span>
        </div>
        <div className="text-right">
          <p className="text-[10px] text-slate-500 uppercase font-bold tracking-tighter">Identity Score</p>
          <p className="text-sm font-bold text-blue-400">{ms.identity_score}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {platforms.map(p => {
          const style = PLATFORM_STYLES[p] || PLATFORM_STYLES.unknown
          return (
            <div key={p} className="glass-sm p-3 flex flex-col items-center text-center">
              <span className="text-xs font-bold px-2.5 py-1 rounded-full mb-2"
                style={{ background: style.bg, color: style.color, border: `1px solid ${style.border}` }}>
                {style.label}
              </span>
              <div className="flex items-center gap-1 text-[10px] text-slate-400">
                <CheckCircle size={10} className="text-green-500" />
                <span>Profile Found</span>
              </div>
            </div>
          )
        })}
        {platforms.length === 0 && (
          <div className="sm:col-span-2 lg:col-span-4 p-4 rounded-xl border border-dashed border-slate-800 text-center">
            <p className="text-xs text-slate-500">No linked social profiles found via username search.</p>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        {hasFaceMatch && (
          <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-green-500/10 border border-green-500/20">
            <Users size={14} className="text-green-400" />
            <span className="text-xs font-medium text-green-400">Face Match Confirmed via OSINT</span>
          </div>
        )}
        {riskFlags.map(flag => (
          <div key={flag} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-red-500/10 border border-red-500/20">
            <AlertTriangle size={14} className="text-red-400" />
            <span className="text-xs font-medium text-red-400">{flag.replace(/_/g, ' ')}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
