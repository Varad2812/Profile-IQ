import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Search, History, ShieldCheck, LogOut, Zap, ChevronRight } from 'lucide-react'
import { motion } from 'framer-motion'
import useAuthStore from '../../store/authStore'

const links = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/analyze', icon: Search, label: 'Analyze Profile' },
  { to: '/history', icon: History, label: 'History' },
]

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  return (
    <aside className="w-56 min-h-screen flex flex-col shrink-0" style={{ background: 'rgba(3,10,25,0.98)', borderRight: '1px solid rgba(59,130,246,0.08)' }}>
      {/* Logo */}
      <div className="px-4 py-5 flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)', boxShadow: '0 0 16px rgba(99,102,241,0.4)' }}>
          <Zap size={15} className="text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-none">ProfileIQ</p>
          <p className="text-slate-600 text-[10px] mt-0.5">Verification System</p>
        </div>
      </div>

      {/* Nav */}
      <div className="px-2 flex-1 space-y-0.5 mt-2">
        <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-2 mb-2">Navigation</p>
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Icon size={15} />
            <span className="flex-1">{label}</span>
            <ChevronRight size={12} className="opacity-30" />
          </NavLink>
        ))}
        {user?.role === 'admin' && (
          <>
            <p className="text-[10px] font-semibold text-slate-600 uppercase tracking-widest px-2 mt-4 mb-2">Admin</p>
            <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <ShieldCheck size={15} />
              <span className="flex-1">Admin Panel</span>
              <ChevronRight size={12} className="opacity-30" />
            </NavLink>
          </>
        )}
      </div>

      {/* User */}
      <div className="p-3 mt-auto">
        <div className="glass-sm p-3 mb-2">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold text-white shrink-0" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)' }}>
              {user?.email?.[0]?.toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-xs text-slate-300 font-medium truncate">{user?.email?.split('@')[0]}</p>
              <span className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ background: user?.role === 'admin' ? 'rgba(139,92,246,0.2)' : 'rgba(59,130,246,0.15)', color: user?.role === 'admin' ? '#a78bfa' : '#60a5fa' }}>
                {user?.role}
              </span>
            </div>
          </div>
        </div>
        <button onClick={() => { logout(); navigate('/login') }} className="nav-link w-full hover:!text-red-400 hover:!bg-red-500/10 hover:!border-red-500/20">
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
