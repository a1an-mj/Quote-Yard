import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import Logo from './Logo'
import ThemeSwitch from './ThemeSwitch'

export default function PublicNav() {
  const { user } = useAuth()
  return (
    <header className="qy-nav">
      <div className="qy-wrap qy-nav__in">
        <Logo />
        <nav className="qy-navlinks qy-nav__links" aria-label="Main" style={{ flex: 1 }}>
          <a className="qy-navlink" href="/#deals">Today's deals</a>
          <a className="qy-navlink" href="/#stores">Stores</a>
          <a className="qy-navlink" href="/#how">How it works</a>
        </nav>
        <div className="qy-row" style={{ marginLeft: 'auto', flexWrap: 'wrap' }}>
          <ThemeSwitch />
          {user ? (
            <Link className="qy-btn qy-btn--primary" to="/home">Open Quote Yard</Link>
          ) : (
            <>
              <Link className="qy-btn qy-btn--ghost" to="/login">Log in</Link>
              <Link className="qy-btn qy-btn--primary" to="/signup">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
