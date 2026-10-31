import Footer from './Footer'
import PublicNav from './PublicNav'

export default function AuthCard({ title, intro, children, footer }) {
  return (
    <>
      <PublicNav />
      <main className="qy-wrap qy-auth">
        <div className="qy-tile qy-tile--pad qy-auth__card">
          <div className="qy-stack" style={{ gap: 8 }}>
            <h1 className="qy-h1">{title}</h1>
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
