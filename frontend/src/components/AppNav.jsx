import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import Logo from './Logo'
import SearchBox from './SearchBox'
import ThemeSwitch from './ThemeSwitch'

export default function AppNav({ search = true }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function leave() {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <header className="qy-nav">
      <div className="qy-wrap qy-nav__in">
        <Logo to="/home" />
        {search && <SearchBox compact />}
        <nav className="qy-navlinks" aria-label="Main">
          <NavLink className={({ isActive }) => `qy-navlink ${isActive ? 'qy-navlink--on' : ''}`} to="/categories">Categories</NavLink>
        </nav>
        <div className="qy-row qy-appnav__user" style={{ flexWrap: 'wrap' }}>
          <ThemeSwitch />
          <span className="qy-small">Hi {user?.first_name}</span>
          <button className="qy-btn qy-btn--ghost" type="button" onClick={leave}>Log out</button>
        </div>
      </div>
    </header>
  )
}

export function Breadcrumb({ current }) {
  return (
    <nav aria-label="Breadcrumb" className="qy-row qy-small" style={{ gap: 8 }}>
      <Link to="/home">Home</Link>
      <span aria-hidden="true">/</span>
      <span>{current}</span>
    </nav>
  )
}
