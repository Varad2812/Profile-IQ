import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Zap, Shield, BarChart3, ArrowRight, CheckCircle, Eye, Network, Brain, Fingerprint, ChevronRight } from 'lucide-react'

const FEATURES = [
  { icon: Brain,       title: 'Multi-Modal AI',         desc: 'Combines face, text, behavior, network and identity signals for comprehensive verification.' },
  { icon: Eye,         title: 'Explainable Results',    desc: 'Every score comes with evidence logs and module breakdowns — no black box decisions.' },
  { icon: Network,     title: 'Cross-Platform Check',   desc: 'Verifies identity consistency across multiple social platforms simultaneously.' },
  { icon: Shield,      title: 'Real-Time Detection',    desc: 'Instant analysis pipeline returns results in seconds with confidence scoring.' },
  { icon: BarChart3,   title: 'Trust Score Engine',     desc: 'Weighted 0–100 trust score with risk classification: Low, Medium, or High.' },
  { icon: Fingerprint, title: 'Identity Verification',  desc: 'Deep identity fingerprinting to detect repurposed or synthetic accounts.' },
]

const STEPS = [
  { n: '01', title: 'Paste Profile URL',   desc: 'Enter any Instagram profile URL into the analyzer.' },
  { n: '02', title: 'AI Runs Analysis',    desc: '6 independent AI modules analyze the profile simultaneously.' },
  { n: '03', title: 'Review Results',      desc: 'Get a trust score, risk level, evidence log and module breakdown.' },
]

const fade = (delay = 0) => ({ initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.5, delay } })

export default function Landing() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(160deg,#020b18 0%,#050f20 50%,#020b18 100%)' }}>
      {/* Ambient blobs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full opacity-5" style={{ background: 'radial-gradient(circle,#3b82f6,transparent)', filter: 'blur(60px)' }} />
        <div className="absolute bottom-1/3 right-1/4 w-80 h-80 rounded-full opacity-5" style={{ background: 'radial-gradient(circle,#6366f1,transparent)', filter: 'blur(60px)' }} />
      </div>

      {/* Navbar */}
      <nav className="relative z-10 flex items-center justify-between px-8 py-4" style={{ borderBottom: '1px solid rgba(59,130,246,0.06)' }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)', boxShadow: '0 0 16px rgba(99,102,241,0.35)' }}>
            <Zap size={15} className="text-white" />
          </div>
          <span className="font-bold text-white">ProfileIQ</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded font-medium ml-1" style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa' }}>BETA</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => navigate('/login')} className="btn-ghost text-sm">Sign In</button>
          <button onClick={() => navigate('/register')} className="btn-primary text-sm">Get Started <ArrowRight size={14} /></button>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center text-center px-6 pt-24 pb-20">
        <motion.div {...fade(0)}>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium mb-6" style={{ background: 'rgba(59,130,246,0.08)', border: '1px solid rgba(59,130,246,0.15)', color: '#60a5fa' }}>
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            AI-Powered Social Profile Verification
            <ChevronRight size={12} />
          </div>
        </motion.div>

        <motion.h1 {...fade(0.1)} className="text-5xl md:text-6xl font-extrabold text-white leading-tight max-w-3xl mb-5">
          Detect Fake Profiles<br />
          <span style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1,#8b5cf6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Before They Deceive
          </span>
        </motion.h1>

        <motion.p {...fade(0.2)} className="text-slate-400 text-lg max-w-xl mb-8 leading-relaxed">
          ProfileIQ uses multi-modal AI to analyze social media profiles and generate a trust score — exposing bots, fake accounts, and synthetic identities in seconds.
        </motion.p>

        <motion.div {...fade(0.3)} className="flex gap-3 flex-wrap justify-center mb-12">
          <button onClick={() => navigate('/register')} className="btn-primary px-6 py-3 text-base">
            Analyze a Profile <ArrowRight size={16} />
          </button>
          <button onClick={() => navigate('/login')} className="btn-ghost px-6 py-3 text-base">
            Sign In
          </button>
        </motion.div>

        {/* Trust indicators */}
        <motion.div {...fade(0.4)} className="flex flex-wrap justify-center gap-5 text-sm text-slate-500">
          {['6 AI Modules', 'Real-time Analysis', 'Evidence Logs', 'Confidence Scoring'].map(t => (
            <div key={t} className="flex items-center gap-1.5">
              <CheckCircle size={13} className="text-emerald-500" /> {t}
            </div>
          ))}
        </motion.div>
      </section>

      {/* How it works */}
      <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-10">
          <p className="text-xs font-semibold text-blue-400 uppercase tracking-widest mb-2">How It Works</p>
          <h2 className="text-2xl font-bold text-white">Three steps to verify any profile</h2>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {STEPS.map(({ n, title, desc }, i) => (
            <motion.div key={n} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.1 }} className="glass p-6 text-center">
              <div className="text-4xl font-black mb-3" style={{ background: 'linear-gradient(135deg,#3b82f6,#6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>{n}</div>
              <h3 className="font-semibold text-white mb-2">{title}</h3>
              <p className="text-sm text-slate-500">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="relative z-10 px-8 py-16 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-10">
          <p className="text-xs font-semibold text-blue-400 uppercase tracking-widest mb-2">Capabilities</p>
          <h2 className="text-2xl font-bold text-white">Everything you need to verify trust</h2>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <motion.div key={title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.07 }} className="glass p-5 hover:scale-[1.02] transition-transform">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center mb-3" style={{ background: 'rgba(59,130,246,0.12)', border: '1px solid rgba(59,130,246,0.2)' }}>
                <Icon size={16} className="text-blue-400" />
              </div>
              <h3 className="font-semibold text-white text-sm mb-1.5">{title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative z-10 px-8 py-20 text-center">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass max-w-2xl mx-auto p-10 glow-blue">
          <h2 className="text-3xl font-bold text-white mb-3">Ready to verify profiles?</h2>
          <p className="text-slate-400 mb-6">Create a free account and run your first analysis in under 30 seconds.</p>
          <button onClick={() => navigate('/register')} className="btn-primary px-8 py-3 text-base">
            Start for Free <ArrowRight size={16} />
          </button>
        </motion.div>
      </section>

      <footer className="relative z-10 text-center py-6 text-xs text-slate-700 border-t" style={{ borderColor: 'rgba(59,130,246,0.06)' }}>
        © 2024 ProfileIQ — AI Profile Verification System
      </footer>
    </div>
  )
}
