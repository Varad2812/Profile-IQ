import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, AlertCircle, ExternalLink, CheckCircle, XCircle,
  AlertTriangle, Info, Cpu, Upload, Link, Image, X, FileImage,
} from 'lucide-react'
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip } from 'recharts'
import TrustGauge from '../components/ui/TrustGauge'
import RiskBadge from '../components/ui/RiskBadge'
import OcrDataSection from '../components/shared/OcrDataSection'
import ProfileIntelligenceSection from '../components/shared/ProfileIntelligenceSection'
import CrossPlatformSection from '../components/shared/CrossPlatformSection'
import ModuleCard, { MODULES } from '../components/shared/ModuleCard'
import { toast } from '../components/ui/Toast'
import api from '../lib/api'

// ─── Constants ────────────────────────────────────────────────────────────────

const EV_CONFIG = {
  critical: { icon: XCircle,       color: '#f87171', bg: 'rgba(239,68,68,0.08)',  border: 'rgba(239,68,68,0.2)',  label: 'Critical' },
  warning:  { icon: AlertTriangle, color: '#fbbf24', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', label: 'Warning' },
  positive: { icon: CheckCircle,   color: '#34d399', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', label: 'Positive' },
}

// ─── Analyzing animation ──────────────────────────────────────────────────────

function AnalyzingAnimation({ mode }) {
  const steps = mode === 'screenshot'
    ? ['Loading screenshot...', 'Extracting profile metadata...', 'Searching linked accounts...', 'Cross-referencing face id...', 'Validating platform presence...', 'Computing trust score...']
    : ['Resolving profile URL...', 'Running OSINT username search...', 'Probing social platforms...', 'Comparing face embeddings...', 'Scoring identity consistency...', 'Computing trust score...']
  const [step, setStep] = useState(0)
  useEffect(() => {
    setStep(0)
    const iv = setInterval(() => setStep(s => (s + 1) % steps.length), 900)
    return () => clearInterval(iv)
  }, [steps.length])
  return (
    <div className="glass p-8 flex flex-col items-center gap-5">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-blue-500/20" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
        <div className="absolute inset-2 rounded-full border-2 border-transparent border-t-indigo-400 animate-spin-slow" />
        <Cpu size={18} className="absolute inset-0 m-auto text-blue-400" />
      </div>
      <div className="text-center">
        <p className="text-white font-semibold mb-1">{mode === 'screenshot' ? 'Analyzing Screenshot' : 'Analyzing Profile'}</p>
        <p className="text-xs text-blue-400 animate-pulse">{steps[step]}</p>
      </div>
      <div className="w-full max-w-xs space-y-2">
        {MODULES.map((m, i) => (
          <div key={m.key} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#3b82f6', animationDelay: `${i * 0.15}s` }} />
            <div className="flex-1 h-1.5 rounded-full skeleton" />
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Drop zone ────────────────────────────────────────────────────────────────

function DropZone({ file, onFile, onClear }) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef()

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f && f.type.startsWith('image/')) onFile(f)
    else toast.warning('Only image files are accepted (JPEG, PNG, WEBP)')
  }, [onFile])

  if (file) {
    return (
      <div className="relative rounded-xl overflow-hidden border" style={{ border: '1px solid rgba(59,130,246,0.25)', background: 'rgba(5,15,35,0.6)' }}>
        <img src={URL.createObjectURL(file)} alt="preview" className="w-full max-h-64 object-contain" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileImage size={14} className="text-blue-400" />
            <span className="text-xs text-white font-medium truncate max-w-[200px]">{file.name}</span>
            <span className="text-[10px] text-slate-400">({(file.size / 1024).toFixed(0)} KB)</span>
          </div>
          <button onClick={onClear} className="w-6 h-6 rounded-full flex items-center justify-center text-white hover:bg-red-500/30 transition-colors" style={{ background: 'rgba(239,68,68,0.2)' }}>
            <X size={12} />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className="rounded-xl border-2 border-dashed p-10 flex flex-col items-center gap-3 cursor-pointer transition-all"
      style={{ borderColor: dragging ? 'rgba(59,130,246,0.6)' : 'rgba(59,130,246,0.2)', background: dragging ? 'rgba(59,130,246,0.06)' : 'rgba(5,15,35,0.4)' }}>
      <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)' }}>
        <Upload size={20} className="text-blue-400" />
      </div>
      <div className="text-center">
        <p className="text-sm font-semibold text-white">Drop screenshot here</p>
        <p className="text-xs text-slate-500 mt-1">or click to browse — JPEG, PNG, WEBP up to 10MB</p>
      </div>
      <input ref={inputRef} type="file" accept="image/*" className="hidden" onChange={e => { if (e.target.files[0]) onFile(e.target.files[0]) }} />
    </div>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function Analyze() {
  const [mode, setMode]     = useState('url')
  const [url, setUrl]       = useState('')
  const [file, setFile]     = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState(null)

  const handleAnalyze = async (e) => {
    e.preventDefault()
    setLoading(true); setError(null); setResult(null)

    try {
      let data
      if (mode === 'screenshot') {
        if (!file) { setError('Please upload a screenshot first.'); setLoading(false); return }
        const form = new FormData()
        form.append('file', file)
        form.append('profile_url', `screenshot:${file.name}`)
        const res = await api.post('/analyze/screenshot', form, { headers: { 'Content-Type': 'multipart/form-data' } })
        data = res.data
      } else {
        if (!url.trim()) { setError('Please enter a profile URL.'); setLoading(false); return }
        let normalizedUrl = url.trim()
        // Auto-prepend https:// if protocol is missing
        if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
          normalizedUrl = 'https://' + normalizedUrl
        }
        const form = new FormData()
        form.append('profile_url', normalizedUrl)
        const res = await api.post('/analyze', form, { headers: { 'Content-Type': 'multipart/form-data' } })
        data = res.data
      }
      setResult(data)
      toast.success(`Analysis complete — Trust score: ${data.trust_score}%`)
    } catch (err) {
      const msg = err.response?.data?.detail?.message
        || err.response?.data?.message
        || err.response?.data?.detail
        || err.message
        || 'Analysis failed. Please try again.'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
      toast.error(typeof msg === 'string' ? msg : 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const radarData = result?.module_scores
    ? MODULES.map(m => ({ name: m.label.split(' ')[0], value: result.module_scores[m.key] || 0 }))
    : []

  const criticals = result?.evidence_logs?.filter(e => e.log_type === 'critical') || []
  const warnings  = result?.evidence_logs?.filter(e => e.log_type === 'warning')  || []
  const positives = result?.evidence_logs?.filter(e => e.log_type === 'positive') || []

  return (
    <div className="max-w-5xl space-y-5">

      {/* Input card */}
      <div className="glass p-6">
        <div className="flex items-center gap-2 mb-4">
          <Search size={15} className="text-blue-400" />
          <h2 className="text-sm font-semibold text-white">Profile Analyzer</h2>
        </div>

        {/* Mode tabs */}
        <div className="flex gap-1 p-1 rounded-xl mb-5 w-fit" style={{ background: 'rgba(5,15,35,0.6)', border: '1px solid rgba(59,130,246,0.12)' }}>
          {[{ id: 'url', label: 'Analyze via URL', icon: Link }, { id: 'screenshot', label: 'Analyze via Screenshot', icon: Image }].map(({ id, label, icon: Icon }) => (
            <button key={id} onClick={() => { setMode(id); setResult(null); setError(null) }}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all"
              style={mode === id
                ? { background: 'linear-gradient(135deg,#3b82f6,#6366f1)', color: 'white', boxShadow: '0 2px 12px rgba(59,130,246,0.3)' }
                : { color: '#64748b' }}>
              <Icon size={13} /> {label}
            </button>
          ))}
        </div>

        <form onSubmit={handleAnalyze} className="space-y-4">
          <AnimatePresence mode="wait">
            {mode === 'url' ? (
              <motion.div key="url" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Profile URL</label>
                <div className="relative">
                  <ExternalLink size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
                  <input value={url} onChange={e => setUrl(e.target.value)} placeholder="instagram.com/username or https://instagram.com/username" className="input-field pl-9" />
                </div>
              </motion.div>
            ) : (
              <motion.div key="screenshot" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }}>
                <label className="text-xs font-medium text-slate-400 mb-1.5 block">Upload Profile Screenshot</label>
                <DropZone file={file} onFile={setFile} onClear={() => setFile(null)} />
              </motion.div>
            )}
          </AnimatePresence>

          <button type="submit" disabled={loading} className="btn-primary">
            {loading
              ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Analyzing...</>
              : <><Search size={14} /> {mode === 'screenshot' ? 'Analyze Screenshot' : 'Analyze Profile'}</>
            }
          </button>
        </form>

        {error && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="flex items-center gap-2 mt-3 p-3 rounded-xl text-xs"
            style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}>
            <AlertCircle size={13} className="shrink-0" /> {error}
          </motion.div>
        )}
      </div>

      {loading && <AnalyzingAnimation mode={mode} />}

      <AnimatePresence>
        {result && !loading && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">

            {/* Hero */}
            <div className="glass p-6" style={{ borderColor: result.risk_level === 'low' ? 'rgba(16,185,129,0.2)' : result.risk_level === 'high' ? 'rgba(239,68,68,0.2)' : 'rgba(245,158,11,0.2)' }}>
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="flex flex-col items-center gap-4">
                  <TrustGauge score={result.trust_score} size={160} />
                  {result.profile_image_b64 && (
                    <div className="w-24 h-24 rounded-xl overflow-hidden border" style={{ border: '1px solid rgba(59,130,246,0.2)' }}>
                      <img src={result.profile_image_b64} alt="profile preview" className="w-full h-full object-cover" />
                    </div>
                  )}
                </div>
                <div className="flex-1 text-center md:text-left">
                  <div className="flex items-center gap-3 justify-center md:justify-start mb-3 flex-wrap">
                    <h3 className="text-xl font-bold text-white">Verification Complete</h3>
                    <RiskBadge level={result.risk_level} size="lg" />
                    <span className="text-[10px] px-2 py-1 rounded-full font-semibold flex items-center gap-1"
                      style={result.input_type === 'screenshot'
                        ? { background: 'rgba(139,92,246,0.15)', color: '#a78bfa', border: '1px solid rgba(139,92,246,0.2)' }
                        : { background: 'rgba(59,130,246,0.12)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.2)' }}>
                      {result.input_type === 'screenshot' ? <Image size={10} /> : <Link size={10} />}
                      {result.input_type === 'screenshot' ? 'Screenshot' : 'URL'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mb-3 break-all">{result.profile_url}</p>
                  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl mb-4 text-xs font-medium"
                    style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.2)', color: '#60a5fa' }}>
                    <Info size={12} /> Confidence: {result.confidence}%
                  </div>
                  <div className="glass-sm p-4">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">AI Executive Summary</p>
                    <p className="text-sm text-slate-300 leading-relaxed">{result.summary}</p>
                  </div>
                </div>
              </div>
            </div>

            {result.ocr_data?.ocr_available && (
              <OcrDataSection
                ocr={result.ocr_data}
                sourceLabel={result.input_type === 'screenshot' ? 'OCR' : 'Browser'}
              />
            )}
            {result.module_scores && <ProfileIntelligenceSection ms={result.module_scores} />}
            {result.module_scores && <CrossPlatformSection ms={result.module_scores} />}

            {/* Module breakdown + Radar */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
              <div className="lg:col-span-3 space-y-2.5">
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Module Breakdown</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {MODULES.map(mod => (
                    <ModuleCard key={mod.key} mod={mod} score={result.module_scores?.[mod.key] ?? 0}
                      faceData={mod.key === 'face_score' ? result.module_scores : null}
                      textData={result.module_scores} />
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
        )}
      </AnimatePresence>

      {!result && !loading && (
        <div className="glass p-10 text-center">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4"
            style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)' }}>
            {mode === 'screenshot' ? <Upload size={22} className="text-blue-400" /> : <Search size={22} className="text-blue-400" />}
          </div>
          <p className="text-white font-semibold mb-1">Ready to analyze</p>
          <p className="text-sm text-slate-500">
            {mode === 'screenshot' ? 'Upload a profile screenshot above to run AI face verification' : 'Enter a profile URL above to run a full AI verification'}
          </p>
        </div>
      )}
    </div>
  )
}
