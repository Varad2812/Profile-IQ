import { Globe, AtSign, Users, Hash, AlertOctagon } from 'lucide-react'

export const PLATFORM_STYLES = {
  instagram: { color: '#e1306c', bg: 'rgba(225,48,108,0.12)', border: 'rgba(225,48,108,0.25)', label: 'Instagram' },
  twitter:   { color: '#1d9bf0', bg: 'rgba(29,155,240,0.12)', border: 'rgba(29,155,240,0.25)', label: 'Twitter / X' },
  linkedin:  { color: '#0a66c2', bg: 'rgba(10,102,194,0.12)', border: 'rgba(10,102,194,0.25)', label: 'LinkedIn' },
  facebook:  { color: '#1877f2', bg: 'rgba(24,119,242,0.12)', border: 'rgba(24,119,242,0.25)', label: 'Facebook' },
  tiktok:    { color: '#ff0050', bg: 'rgba(255,0,80,0.12)',   border: 'rgba(255,0,80,0.25)',   label: 'TikTok' },
  unknown:   { color: '#64748b', bg: 'rgba(100,116,139,0.12)',border: 'rgba(100,116,139,0.25)',label: 'Unknown Platform' },
}

export default function OcrDataSection({ ocr, sourceLabel = 'OCR' }) {
  if (!ocr) return null
  const hasData = ocr.username || ocr.bio || ocr.followers || ocr.platform !== 'unknown'
  const ps = PLATFORM_STYLES[ocr.platform] || PLATFORM_STYLES.unknown

  return (
    <div className="glass p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <p className="text-xs font-semibold text-white uppercase tracking-wider">Extracted Profile Data</p>
          <span className="text-[9px] px-1.5 py-0.5 rounded font-bold uppercase"
            style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa' }}>{sourceLabel}</span>
        </div>
        {ocr.confidence > 0 && (
          <span className="text-[10px] text-slate-500">{Math.round(ocr.confidence * 100)}% confidence</span>
        )}
      </div>

      {ocr.ocr_status === 'unavailable' && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl mb-3"
          style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}>
          <AlertOctagon size={14} className="text-yellow-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-yellow-400 mb-0.5">Tesseract OCR Not Installed</p>
            <p className="text-xs text-slate-400">Install Tesseract on the server to enable text extraction from screenshots.</p>
            <a href="https://github.com/UB-Mannheim/tesseract/wiki" target="_blank" rel="noreferrer"
              className="text-xs text-blue-400 hover:text-blue-300 mt-1 inline-block">Download Tesseract →</a>
          </div>
        </div>
      )}

      {ocr.ocr_status === 'error' && (
        <div className="flex items-start gap-2.5 p-3 rounded-xl mb-3"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
          <AlertOctagon size={14} className="text-red-400 shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-red-400 mb-0.5">OCR Extraction Failed</p>
            <p className="text-xs text-slate-400">{ocr.error || 'An unexpected error occurred during OCR processing.'}</p>
          </div>
        </div>
      )}

      {hasData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="glass-sm p-3">
            <div className="flex items-center gap-1.5 mb-1">
              <Globe size={11} className="text-slate-500" />
              <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Platform</p>
            </div>
            <span className="text-xs font-bold px-2.5 py-1 rounded-full"
              style={{ background: ps.bg, color: ps.color, border: `1px solid ${ps.border}` }}>
              {ps.label}
            </span>
          </div>

          {ocr.username && (
            <div className="glass-sm p-3">
              <div className="flex items-center gap-1.5 mb-1">
                <AtSign size={11} className="text-slate-500" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Username</p>
              </div>
              <p className="text-sm font-semibold text-white">@{ocr.username}</p>
            </div>
          )}

          {(ocr.followers || ocr.following || ocr.posts) && (
            <div className="glass-sm p-3 sm:col-span-2">
              <div className="flex items-center gap-1.5 mb-2">
                <Users size={11} className="text-slate-500" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Stats</p>
              </div>
              <div className="flex gap-4 flex-wrap">
                {ocr.followers && <div><p className="text-sm font-bold text-white">{ocr.followers}</p><p className="text-[10px] text-slate-500">Followers</p></div>}
                {ocr.following && <div><p className="text-sm font-bold text-white">{ocr.following}</p><p className="text-[10px] text-slate-500">Following</p></div>}
                {ocr.posts    && <div><p className="text-sm font-bold text-white">{ocr.posts}</p><p className="text-[10px] text-slate-500">Posts</p></div>}
              </div>
            </div>
          )}

          {ocr.bio && (
            <div className="glass-sm p-3 sm:col-span-2">
              <div className="flex items-center gap-1.5 mb-1">
                <Hash size={11} className="text-slate-500" />
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Bio</p>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{ocr.bio}</p>
            </div>
          )}
        </div>
      )}

      {!hasData && ocr.ocr_available && (
        <p className="text-xs text-slate-600 italic">No structured profile data could be extracted from this screenshot.</p>
      )}
    </div>
  )
}
