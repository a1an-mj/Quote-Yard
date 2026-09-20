import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Menu, X, Tag, LogOut } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const links = [
  { to: '/dashboard', label: 'Home' },
  { to: '/search', label: 'Search' },
  { to: '/dashboard#deals', label: 'Deals' },
]

export default function Navbar({ variant = 'app' }) {
  const [open, setOpen] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isApp = variant === 'app'

  function handleLogout() {
    logout()
    setOpen(false)
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b-2 border-ink bg-ivory/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to={isApp ? '/dashboard' : '/'} className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-ink bg-terracotta text-ivory">
            <Tag size={18} strokeWidth={2.5} />
          </span>
          <span className="font-display text-lg font-bold tracking-tight text-ink">Quote Yard</span>
        </Link>

        {isApp && (
          <>
            <nav className="hidden items-center gap-1 md:flex">
              {links.map((l) => (
                <NavLink
                  key={l.label}
                  to={l.to}
                  className={({ isActive }) =>
                    `rounded-full px-4 py-2 font-body text-sm font-semibold transition-colors ${
                      isActive ? 'bg-ink text-ivory' : 'text-walnut hover:bg-ink/5'
                    }`
                  }
                >
                  {l.label}
                </NavLink>
              ))}
            </nav>

            <div className="hidden items-center gap-3 md:flex">
              <div className="flex items-center gap-2 rounded-full border-2 border-ink bg-ivory px-3 py-1.5 shadow-brutal-sm">
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-olive font-display text-xs font-bold text-ivory">
                  {user?.name?.[0]?.toUpperCase() || 'Q'}
                </span>
                <span className="font-body text-sm font-semibold text-ink">{user?.name}</span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1.5 rounded-full px-3 py-2 font-body text-sm font-semibold text-walnut transition-colors hover:bg-ink/5 hover:text-ink"
              >
                <LogOut size={16} />
                Logout
              </button>
            </div>

            <button
              onClick={() => setOpen((o) => !o)}
              className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-ink md:hidden"
              aria-label="Toggle menu"
            >
              {open ? <X size={20} /> : <Menu size={20} />}
            </button>
          </>
        )}
      </div>

      {isApp && open && (
        <div className="border-t-2 border-ink bg-ivory px-4 pb-5 pt-3 md:hidden animate-fade-up">
          <nav className="mb-3 flex flex-col gap-1">
            {links.map((l) => (
              <NavLink
                key={l.label}
                to={l.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `rounded-chunky-sm px-4 py-3 font-body text-sm font-semibold ${
                    isActive ? 'bg-ink text-ivory' : 'text-walnut hover:bg-ink/5'
                  }`
                }
              >
                {l.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center justify-between rounded-chunky-sm border-2 border-ink px-4 py-3">
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-olive font-display text-xs font-bold text-ivory">
                {user?.name?.[0]?.toUpperCase() || 'Q'}
              </span>
              <span className="font-body text-sm font-semibold text-ink">{user?.name}</span>
            </div>
            <button onClick={handleLogout} className="text-walnut">
              <LogOut size={18} />
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
