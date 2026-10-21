import { motion } from 'framer-motion'

export function StatCard({ label, value, icon: Icon, color = '#3b82f6', sub, index = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07 }}
      className="glass p-5 hover:scale-[1.02] transition-transform duration-200 cursor-default"
      style={{ boxShadow: `0 0 25px ${color}12` }}
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: `${color}18`, border: `1px solid ${color}25` }}>
          <Icon size={16} style={{ color }} />
        </div>
        {sub && <span className="text-[10px] px-2 py-0.5 rounded-full font-medium" style={{ background: `${color}15`, color }}>{sub}</span>}
      </div>
      <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
      <p className="text-xs text-slate-500 mt-1 font-medium">{label}</p>
    </motion.div>
  )
}

export function SkeletonCard() {
  return (
    <div className="glass p-5">
      <div className="w-9 h-9 rounded-xl skeleton mb-4" />
      <div className="h-7 w-16 skeleton mb-2" />
      <div className="h-3 w-24 skeleton" />
    </div>
  )
}
