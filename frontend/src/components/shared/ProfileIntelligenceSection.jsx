import { Brain, Tag, Globe, Activity, Users } from 'lucide-react'
import { PLATFORM_STYLES } from './OcrDataSection'

export const PROFILE_TYPE_STYLES = {
  individual:    { color: '#34d399', bg: 'rgba(16,185,129,0.12)',  border: 'rgba(16,185,129,0.25)',  label: 'Individual',    icon: '👤' },
  public_figure: { color: '#f472b6', bg: 'rgba(236,72,153,0.12)', border: 'rgba(236,72,153,0.25)', label: 'Public Figure', icon: '🌟' },
  influencer:    { color: '#60a5fa', bg: 'rgba(59,130,246,0.12)',  border: 'rgba(59,130,246,0.25)',  label: 'Influencer',    icon: '⭐' },
  business:      { color: '#a78bfa', bg: 'rgba(139,92,246,0.12)',  border: 'rgba(139,92,246,0.25)',  label: 'Business',      icon: '🏢' },
  suspicious:    { color: '#f87171', bg: 'rgba(239,68,68,0.12)',   border: 'rgba(239,68,68,0.25)',   label: 'Suspicious',    icon: '⚠️' },
  unknown:       { color: '#64748b', bg: 'rgba(100,116,139,0.12)', border: 'rgba(100,116,139,0.25)', label: 'Unknown',       icon: '❓' },
}

export default function ProfileIntelligenceSection({ ms }) {
  if (!ms) return null
  const ptype = ms.profile_type || 'unknown'
  const ps = PROFILE_TYPE_STYLES[ptype] || PROFILE_TYPE_STYLES.unknown
  const entities = typeof ms.profile_entities === 'string' ? ms.profile_entities.split(',').filter(Boolean) : []
  const bflags = typeof ms.behavior_flags === 'string' ? ms.behavior_flags.split(',').filter(Boolean) : []
  const hasRealBehavior = ms.behavior_source && ms.behavior_source !== 'mock'
  const ps_platform = PLATFORM_STYLES[ms.platform] || PLATFORM_STYLES.unknown

  return (
    <div className="glass p-5">
      <div className="flex items-center gap-2 mb-4">
        <Brain size={15} className="text-purple-400" />
        <p className="text-xs font-semibold text-white uppercase tracking-wider">Profile Intelligence</p>
        <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase"
          style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa' }}>AI</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="glass-sm p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Tag size={11} className="text-slate-500" />
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Profile Type</p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-base">{ps.icon}</span>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full"
              style={{ background: ps.bg, color: ps.color, border: `1px solid ${ps.border}` }}>
              {ps.label}
            </span>
            {ms.profile_type_confidence > 0 && (
              <span className="text-[10px] text-slate-500">{Math.round(ms.profile_type_confidence * 100)}% conf</span>
            )}
          </div>
        </div>

        <div className="glass-sm p-3">
          <div className="flex items-center gap-1.5 mb-2">
            <Globe size={11} className="text-slate-500" />
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Detected Platform</p>
          </div>
          <span className="text-xs font-bold px-2.5 py-1 rounded-full"
            style={{ background: ps_platform.bg, color: ps_platform.color, border: `1px solid ${ps_platform.border}` }}>
            {ps_platform.label}
          </span>
        </div>

        {hasRealBehavior && (
          <div className="glass-sm p-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Activity size={11} className="text-slate-500" />
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Behavior</p>
              <span className="text-[9px] px-1 py-0.5 rounded font-bold"
                style={{ background: 'rgba(16,185,129,0.12)', color: '#34d399' }}>ML</span>
            </div>
            <p className="text-xs font-bold"
              style={{ color: ms.behavior_score >= 70 ? '#10b981' : ms.behavior_score >= 45 ? '#f59e0b' : '#ef4444' }}>
              Score: {ms.behavior_score}%
            </p>
            {bflags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {bflags.slice(0, 3).map(f => (
                  <span key={f} className="text-[9px] px-1.5 py-0.5 rounded"
                    style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.2)' }}>
                    {f.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {entities.length > 0 && (
          <div className="glass-sm p-3 sm:col-span-2">
            <div className="flex items-center gap-1.5 mb-2">
              <Users size={11} className="text-slate-500" />
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Identified Entities</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {entities.map(e => (
                <span key={e} className="text-xs px-2.5 py-1 rounded-full"
                  style={{ background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.2)' }}>
                  {e}
                </span>
              ))}
            </div>
          </div>
        )}

        {ms.profile_summary && (
          <div className="glass-sm p-3 sm:col-span-2">
            <div className="flex items-center gap-1.5 mb-1.5">
              <Brain size={11} className="text-slate-500" />
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">AI Profile Summary</p>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed">{ms.profile_summary}</p>
          </div>
        )}
      </div>
    </div>
  )
}
