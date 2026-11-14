import Footer from './Footer'
import PublicNav from './PublicNav'
import { MARK } from './brand'

// The logo's eyes alone, big, on a red panel. They glance right when the page opens.
function EyesPanel() {
  return (
    <div className="qy-auth__eyes" aria-hidden="true">
      <svg viewBox="28 72 200 104" focusable="false">
        <path className="qy-auth__whites" d={MARK.eyes} />
        <path className="qy-auth__pupils" d={MARK.pupils} />
      </svg>
    </div>
  )
}

export default function AuthCard({ title, intro, children, footer, eyes = false }) {
  return (
    <>
      <PublicNav />
      <main className={`qy-wrap qy-auth${eyes ? ' qy-auth--eyes' : ''}`}>
        {eyes && <EyesPanel />}
        <div className="qy-tile qy-tile--pad qy-auth__card">
          <div className="qy-stack" style={{ gap: 8 }}>
            <h1 className={eyes ? 'qy-h1 qy-brand-type' : 'qy-h1'}>{title}</h1>
            {intro && <p className="qy-body">{intro}</p>}
          </div>
          {children}
          {footer && <p className="qy-small">{footer}</p>}
        </div>
      </main>
      <Footer />
    </>
  )
}
