import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react'

const ICONS = {
  success: CheckCircle,
  error:   XCircle,
  warning: AlertTriangle,
  info:    Info,
}

const STYLES = {
  success: { color: '#34d399', bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.25)' },
  error:   { color: '#f87171', bg: 'rgba(239,68,68,0.1)',   border: 'rgba(239,68,68,0.25)' },
  warning: { color: '#fbbf24', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.25)' },
  info:    { color: '#60a5fa', bg: 'rgba(59,130,246,0.1)',  border: 'rgba(59,130,246,0.25)' },
}

// ── Toast store (module-level singleton, no external lib needed) ──────────────

let _listeners = []
let _toasts = []
let _nextId = 0

export function toast(message, type = 'info', duration = 4000) {
  const id = ++_nextId
  _toasts = [..._toasts, { id, message, type }]
  _listeners.forEach(fn => fn(_toasts))
  setTimeout(() => {
    _toasts = _toasts.filter(t => t.id !== id)
    _listeners.forEach(fn => fn(_toasts))
  }, duration)
}

toast.success = (msg, dur) => toast(msg, 'success', dur)
toast.error   = (msg, dur) => toast(msg, 'error',   dur)
toast.warning = (msg, dur) => toast(msg, 'warning', dur)
toast.info    = (msg, dur) => toast(msg, 'info',    dur)

// ── ToastContainer — mount once in App.jsx ────────────────────────────────────

export default function ToastContainer() {
  const [toasts, setToasts] = useState([])

  useEffect(() => {
    _listeners.push(setToasts)
    return () => { _listeners = _listeners.filter(fn => fn !== setToasts) }
  }, [])

  const dismiss = (id) => {
    _toasts = _toasts.filter(t => t.id !== id)
    _listeners.forEach(fn => fn(_toasts))
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 pointer-events-none">
      <AnimatePresence>
        {toasts.map(t => {
          const Icon = ICONS[t.type] || Info
          const s = STYLES[t.type] || STYLES.info
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 60, scale: 0.95 }}
              animate={{ opacity: 1, x: 0,  scale: 1 }}
              exit={{ opacity: 0, x: 60, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl shadow-xl max-w-sm"
              style={{ background: 'rgba(10,20,45,0.95)', border: `1px solid ${s.border}`, backdropFilter: 'blur(12px)' }}
            >
              <Icon size={15} style={{ color: s.color }} className="shrink-0 mt-0.5" />
              <p className="text-xs text-slate-200 flex-1 leading-relaxed">{t.message}</p>
              <button onClick={() => dismiss(t.id)} className="text-slate-600 hover:text-slate-400 transition-colors shrink-0">
                <X size={13} />
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
