import { NavLink } from 'react-router-dom'
import { Home, Search, Tags, User } from 'lucide-react'

const items = [
  { to: '/dashboard', label: 'Home', icon: Home },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/dashboard#deals', label: 'Deals', icon: Tags },
  { to: '/profile', label: 'Profile', icon: User },
]

export default function BottomNav() {
  return (
    <nav className="fixed inset-x-0 bottom-0 z-40 border-t-2 border-ink bg-ivory px-3 pb-[env(safe-area-inset-bottom,0px)] md:hidden">
      <div className="mx-auto flex max-w-md items-center justify-between py-2">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={label}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-0.5 rounded-chunky-sm px-4 py-1.5 font-body text-[11px] font-semibold transition-colors ${
                isActive ? 'text-terracotta' : 'text-walnut/60'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors ${
                    isActive ? 'bg-terracotta text-ivory' : ''
                  }`}
                >
                  <Icon size={19} />
                </span>
                {label}
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
