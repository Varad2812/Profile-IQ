import { Bell, Cpu } from 'lucide-react'
import useAuthStore from '../../store/authStore'

export default function Topbar({ title, subtitle }) {
  const { user } = useAuthStore()
  return (
    <header className="h-14 flex items-center justify-between px-6 shrink-0" style={{ background: 'rgba(3,10,25,0.9)', borderBottom: '1px solid rgba(59,130,246,0.08)', backdropFilter: 'blur(12px)' }}>
      <div>
        <h1 className="text-sm font-semibold text-white">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium" style={{ background: 'rgba(16,185,129,0.1)', color: '#34d399', border: '1px solid rgba(16,185,129,0.15)' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          System Online
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium" style={{ background: 'rgba(59,130,246,0.1)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.15)' }}>
          <Cpu size={11} />
          AI Ready
        </div>
        <button className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors" style={{ background: 'rgba(59,130,246,0.06)', border: '1px solid rgba(59,130,246,0.1)' }}>
          <Bell size={14} />
        </button>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold text-white" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)' }}>
          {user?.email?.[0]?.toUpperCase()}
        </div>
      </div>
    </header>
  )
}
