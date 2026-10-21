import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronUp } from 'lucide-react'

export const MODULES = [
  { key: 'face_score',        label: 'Face Authenticity',     icon: '👤', desc: 'Detects AI-generated, stolen, or manipulated profile photos using GAN artifact analysis and DeepFace.' },
  { key: 'text_score',        label: 'Text Analysis',         icon: '📝', desc: 'Analyzes caption language, writing style consistency, and templated or auto-generated content.' },
  { key: 'behavior_score',    label: 'Behavior Analysis',     icon: '📊', desc: 'Examines posting frequency, timing patterns, and engagement metrics for bot-like behavior.' },
  { key: 'network_score',     label: 'Network Analysis',      icon: '🔗', desc: 'Evaluates follower/following ratios and the authenticity of network connections.' },
  { key: 'consistency_score', label: 'Consistency Check',     icon: '🔍', desc: 'Checks for inconsistencies in account metadata, bio changes, and activity history.' },
  { key: 'identity_score',    label: 'Identity Verification', icon: '🪪', desc: 'Cross-platform identity fingerprinting to detect repurposed or synthetic accounts.' },
]

function ScoreBar({ value, color }) {
  return (
    <div className="score-bar-track mt-2">
      <div className="score-bar-fill" style={{ width: `${value}%`, background: color }} />
    </div>
  )
}

export default function ModuleCard({ mod, score, faceData, textData }) {
  const [open, setOpen] = useState(false)
  const color = score >= 70 ? '#10b981' : score >= 45 ? '#f59e0b' : '#ef4444'
  const isFace = mod.key === 'face_score'
  const isText = mod.key === 'text_score'
  const isBehavior = mod.key === 'behavior_score'

  const faceFlags    = typeof faceData?.face_flags === 'string' ? faceData.face_flags.split(',').filter(Boolean) : []
  const isFaceLive   = faceData?.face_source === 'deepface'
  const textFlags    = typeof textData?.text_flags === 'string' ? textData.text_flags.split(',').filter(Boolean) : []
  const isTextLive   = textData?.text_source && textData.text_source !== 'mock'
  const scamKeywords = typeof textData?.text_scam_keywords === 'string' ? textData.text_scam_keywords.split(',').filter(Boolean) : []
  const classification = textData?.text_classification || 'unknown'
  const classColor = { normal: '#34d399', suspicious: '#fbbf24', scam: '#f87171', unknown: '#64748b' }

  return (
    <div className="glass-sm p-4 hover:border-blue-500/20 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <span className="text-lg">{mod.icon}</span>
          <div>
            <div className="flex items-center gap-1.5 flex-wrap">
              <p className="text-sm font-semibold text-white">{mod.label}</p>
              {isFace && isFaceLive && (
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide"
                  style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399' }}>LIVE AI</span>
              )}
              {isText && isTextLive && (
                <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wide"
                  style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc' }}>NLP</span>
              )}
            </div>
            <p className="text-xs font-bold mt-0.5" style={{ color }}>{score}%</p>
          </div>
        </div>
        <button onClick={() => setOpen(!open)} className="text-slate-600 hover:text-slate-400 transition-colors mt-0.5">
          {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      <ScoreBar value={score} color={color} />

      {/* Face metadata */}
      {isFace && faceData && (faceData.face_age > 0 || faceData.face_gender !== 'unknown') && (
        <div className="flex flex-wrap gap-1.5 mt-2.5">
          {faceData.face_age > 0 && (
            <span className="text-[10px] px-2 py-0.5 rounded-full"
              style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.15)' }}>
              Age ~{faceData.face_age}
            </span>
          )}
          {faceData.face_gender !== 'unknown' && (
            <span className="text-[10px] px-2 py-0.5 rounded-full"
              style={{ background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.15)' }}>
              {faceData.face_gender}
            </span>
          )}
          {faceData.face_emotion && faceData.face_emotion !== 'unknown' && (
            <span className="text-[10px] px-2 py-0.5 rounded-full"
              style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.15)' }}>
              {faceData.face_emotion}
            </span>
          )}
        </div>
      )}
      {isFace && faceFlags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {faceFlags.map(flag => (
            <span key={flag} className="text-[9px] px-1.5 py-0.5 rounded font-medium"
              style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.15)' }}>
              ⚠ {flag.replace(/_/g, ' ')}
            </span>
          ))}
        </div>
      )}

      {/* Text metadata */}
      {isText && textData && isTextLive && (
        <div className="mt-2.5 space-y-2">
          <div className="flex flex-wrap gap-1.5">
            <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold"
              style={{ background: `${classColor[classification]}18`, color: classColor[classification], border: `1px solid ${classColor[classification]}30` }}>
              {classification}
            </span>
            {textData.text_scam_prob > 0 && (
              <span className="text-[10px] px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.15)' }}>
                Scam {Math.round(textData.text_scam_prob * 100)}%
              </span>
            )}
            {textData.text_ai_prob > 0.2 && (
              <span className="text-[10px] px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(245,158,11,0.1)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.15)' }}>
                AI-gen {Math.round(textData.text_ai_prob * 100)}%
              </span>
            )}
          </div>
          {scamKeywords.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {scamKeywords.map(kw => (
                <span key={kw} className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                  style={{ background: 'rgba(239,68,68,0.12)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
                  🚩 {kw}
                </span>
              ))}
            </div>
          )}
          {textFlags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {textFlags.map(flag => (
                <span key={flag} className="text-[9px] px-1.5 py-0.5 rounded font-medium"
                  style={{ background: 'rgba(245,158,11,0.08)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.15)' }}>
                  ⚠ {flag.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Behavior metadata */}
      {isBehavior && textData?.behavior_source && textData.behavior_source !== 'mock' && (
        <div className="mt-2.5">
          <div className="flex flex-wrap gap-1.5 mb-1.5">
            <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase"
              style={{ background: 'rgba(16,185,129,0.12)', color: '#34d399' }}>IsolationForest</span>
            <span className="text-[10px] text-slate-500">anomaly={textData.behavior_anomaly_score?.toFixed(3)}</span>
          </div>
          {textData.behavior_flags && typeof textData.behavior_flags === 'string' &&
            textData.behavior_flags.split(',').filter(Boolean).map(f => (
              <span key={f} className="text-[9px] px-1.5 py-0.5 rounded font-medium mr-1"
                style={{ background: 'rgba(245,158,11,0.08)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.15)' }}>
                ⚠ {f.replace(/_/g, ' ')}
              </span>
            ))
          }
        </div>
      )}

      <AnimatePresence>
        {open && (
          <motion.p initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }} className="text-xs text-slate-500 mt-2.5 leading-relaxed overflow-hidden">
            {mod.desc}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}
