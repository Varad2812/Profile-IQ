import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, Image, Link } from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import TrustGauge from '../components/ui/TrustGauge'
import RiskBadge from '../components/ui/RiskBadge'
import OcrDataSection from '../components/shared/OcrDataSection'
import ProfileIntelligenceSection from '../components/shared/ProfileIntelligenceSection'
import CrossPlatformSection from '../components/shared/CrossPlatformSection'
import ModuleCard, { MODULES } from '../components/shared/ModuleCard'
import { toast } from '../components/ui/Toast'
import api from '../lib/api'

const EV_CONFIG = {
  critical: { icon: XCircle,       color: '#f87171', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  label: 'Critical' },
  warning:  { icon: AlertTriangle, color: '#fbbf24', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', label: 'Warning' },
  positive: { icon: CheckCircle,   color: '#34d399', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', label: 'Positive' },
}

export default function AnalysisDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/analysis/${id}`)
      .then(({ data }) => setData(data))
      .catch((err) => {
        const msg = err.response?.data?.detail?.message || err.response?.data?.message || err.response?.data?.detail || 'Failed to load analysis'
        toast.error(msg)
        setData({ error: true, message: msg })
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="max-w-5xl space-y-4">
      <div className="h-8 w-32 skeleton" />
      <div className="glass h-48 skeleton" />
      <div className="grid grid-cols-2 gap-4">{Array(4).fill(0).map((_, i) => <div key={i} className="glass h-24 skeleton" />)}</div>
    </div>
  )

  if (!data || data.error) return (
    <div className="text-center py-20 p-6 glass">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-5">
        <XCircle size={32} className="text-red-500" />
      </div>
      <p className="text-white font-bold text-lg mb-2">Analysis error</p>
      <p className="text-slate-500 mb-6 max-w-sm mx-auto">{data?.message || 'The requested analysis could not be found or loaded.'}</p>
      <button onClick={() => navigate('/history')} className="btn-primary text-xs px-8">← Back to History</button>
    </div>
  )

  const radarData = MODULES.map(m => ({ name: m.label.split(' ')[0], value: data.module_scores?.[m.key] || 0 }))
  const criticals = data.evidence_logs?.filter(e => e.log_type === 'critical') || []
  const warnings  = data.evidence_logs?.filter(e => e.log_type === 'warning')  || []
  const positives = data.evidence_logs?.filter(e => e.log_type === 'positive') || []

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="max-w-5xl space-y-5">
      <button onClick={() => navigate('/history')} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors">
        <ArrowLeft size={13} /> Back to History
      </button>

      {/* Hero */}
      <div className="glass p-6" style={{ borderColor: data.risk_level === 'low' ? 'rgba(16,185,129,0.2)' : data.risk_level === 'high' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)' }}>
        <div className="flex flex-col md:flex-row items-center gap-8">
          <div className="flex flex-col items-center gap-4">
            <TrustGauge score={data.trust_score} size={160} />
            {data.profile_image_b64 && (
              <div className="w-24 h-24 rounded-xl overflow-hidden border" style={{ border: '1px solid rgba(59,130,246,0.2)' }}>
                <img src={data.profile_image_b64} alt="preview" className="w-full h-full object-cover" />
              </div>
            )}
          </div>
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center gap-3 justify-center md:justify-start mb-3 flex-wrap">
              <h2 className="text-xl font-bold text-white">Analysis Result</h2>
              <RiskBadge level={data.risk_level} size="lg" />
              <span className="text-[10px] px-2 py-1 rounded-full font-semibold flex items-center gap-1"
                style={data.input_type === 'screenshot'
                  ? { background: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.2)' }
                  : { background: 'rgba(59,130,246,0.12)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)' }}>
                {data.input_type === 'screenshot' ? <Image size={10} /> : <Link size={10} />}
                {data.input_type === 'screenshot' ? 'Screenshot' : 'URL'}
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-1 break-all">{data.profile_url}</p>
            <p className="text-[10px] text-slate-600 mb-4 uppercase font-bold tracking-widest">{new Date(data.created_at).toLocaleString()}</p>
            <div className="glass-sm p-4">
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">AI Executive Summary</p>
              <p className="text-sm text-slate-300 leading-relaxed">{data.summary}</p>
            </div>
          </div>
        </div>
      </div>

      {data.ocr_data?.ocr_available && <OcrDataSection ocr={data.ocr_data} sourceLabel={data.input_type === 'screenshot' ? 'OCR' : 'Browser'} />}
      {data.module_scores && <ProfileIntelligenceSection ms={data.module_scores} />}
      {data.module_scores && <CrossPlatformSection ms={data.module_scores} />}

      {/* Module breakdown + Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <div className="lg:col-span-3 space-y-2.5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Module Breakdown</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {MODULES.map(mod => (
              <ModuleCard key={mod.key} mod={mod} score={data.module_scores?.[mod.key] || 0}
                faceData={data.module_scores} textData={data.module_scores} />
            ))}
          </div>
        </div>
        <div className="lg:col-span-2 glass p-5">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Radar Overview</p>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(59,130,246,0.1)" />
              <PolarAngleAxis dataKey="name" tick={{ fill: '#475569', fontSize: 10 }} />
              <Radar dataKey="value" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} strokeWidth={2} dot={{ fill: '#3b82f6', r: 3 }} />
              <Tooltip contentStyle={{ background: '#0a1a35', border: '1px solid rgba(59,130,246,0.2)', borderRadius: 8, color: '#e2e8f0', fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Evidence log */}
      <div className="glass p-5">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-4">Evidence Log</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[['critical', criticals], ['warning', warnings], ['positive', positives]].map(([type, logs]) => {
            const cfg = EV_CONFIG[type]; const Icon = cfg.icon
            return (
              <div key={type}>
                <div className="flex items-center gap-1.5 mb-2.5">
                  <Icon size={13} style={{ color: cfg.color }} />
                  <p className="text-xs font-semibold" style={{ color: cfg.color }}>{cfg.label}s ({logs.length})</p>
                </div>
                <div className="space-y-2">
                  {logs.length === 0
                    ? <p className="text-xs text-slate-600 italic">None detected</p>
                    : logs.map((ev, i) => (
                      <div key={i} className="p-2.5 rounded-lg" style={{ background: cfg.bg, border: `1px solid ${cfg.border}` }}>
                        <p className="text-[10px] font-semibold mb-0.5" style={{ color: cfg.color }}>{ev.module}</p>
                        <p className="text-xs text-slate-400 leading-relaxed">{ev.message}</p>
                      </div>
                    ))}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}
