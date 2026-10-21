import { Outlet, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

const META = {
  '/dashboard':  { title: 'Dashboard', subtitle: 'Overview of your verification activity' },
  '/analyze':    { title: 'Profile Analysis', subtitle: 'Run AI-powered profile verification' },
  '/history':    { title: 'Analysis History', subtitle: 'All past verification results' },
  '/admin':      { title: 'Admin Panel', subtitle: 'System management and statistics' },
}

export default function AppLayout() {
  const { pathname } = useLocation()
  let meta = META[pathname]
  
  // Dynamic route matching for analysis detail
  if (!meta && pathname.startsWith('/analysis/')) {
    meta = { title: 'Analysis Result', subtitle: 'Detailed verification evidence' }
  }
  
  if (!meta) meta = { title: 'ProfileIQ' }

  return (
    <div className="flex min-h-screen" style={{ background: 'linear-gradient(160deg,#020b18 0%,#050f20 60%,#020b18 100%)' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <main className="flex-1 p-6 overflow-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
