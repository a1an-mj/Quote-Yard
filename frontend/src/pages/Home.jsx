import { useNavigate } from 'react-router-dom'
import AuthCard from '../components/AuthCard'
import { useAuth } from '../lib/auth'

// Placeholder until the logged-in pages are built.
export default function Home() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function leave() {
    await logout()
    navigate('/', { replace: true })
  }

  return (
    <AuthCard title={`Hi ${user.first_name}`} intro={`Signed in as ${user.email}. Search and product pages come next.`}>
      <button className="qy-btn" type="button" onClick={leave}>Log out</button>
    </AuthCard>
  )
}
