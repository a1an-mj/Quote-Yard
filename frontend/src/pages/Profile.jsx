import { useNavigate } from 'react-router-dom'
import { LogOut, Mail, Phone, ShieldCheck } from 'lucide-react'
import Navbar from '../components/Navbar'
import BottomNav from '../components/BottomNav'
import Button from '../components/Button'
import { useAuth } from '../context/AuthContext'

export default function Profile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-ivory pb-24 md:pb-12">
      <Navbar variant="app" />

      <div className="mx-auto max-w-2xl px-4 pt-8 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 rounded-chunky border-2 border-ink bg-terracotta p-6 text-ivory shadow-brutal">
          <span className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-ivory bg-ink font-display text-2xl font-bold">
            {user?.name?.[0]?.toUpperCase() || 'Q'}
          </span>
          <div>
            <p className="font-display text-2xl font-bold">{user?.name}</p>
            <p className="font-body text-sm text-ivory/80">
              {user?.method === 'google' ? 'Signed in with Google' : 'Quote Yard account'}
            </p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center gap-3 rounded-chunky-sm border-2 border-ink bg-ivory p-4 shadow-brutal-sm">
            <Mail size={18} className="text-terracotta" />
            <span className="font-body text-sm font-medium text-ink">{user?.email}</span>
          </div>
          <div className="flex items-center gap-3 rounded-chunky-sm border-2 border-ink bg-ivory p-4 shadow-brutal-sm">
            <Phone size={18} className="text-terracotta" />
            <span className="font-body text-sm font-medium text-ink">+91 98765 43210</span>
          </div>
          <div className="flex items-center gap-3 rounded-chunky-sm border-2 border-ink bg-ivory p-4 shadow-brutal-sm">
            <ShieldCheck size={18} className="text-olive" />
            <span className="font-body text-sm font-medium text-ink">Mock session &mdash; prototype only</span>
          </div>
        </div>

        <Button onClick={handleLogout} variant="dark" size="lg" className="mt-8 w-full">
          <LogOut size={18} />
          Logout
        </Button>
      </div>

      <BottomNav />
    </div>
  )
}
