import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'
import { useAuth } from '../../lib/auth'

export default function Login() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const { setUser } = useAuth()
  const [email, setEmail] = useState(state?.email ?? '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      setUser(await api('/auth/login', { method: 'POST', body: { email, password } }))
      navigate(state?.from ?? '/home', { replace: true })
    } catch (err) {
      if (err.detail === 'email_not_verified') {
        await api('/auth/resend-code', { method: 'POST', body: { email } }).catch(() => {})
        navigate('/verify', { state: { email } })
        return
      }
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Log in"
      footer={<>New here? <Link className="qy-link" to="/signup">Create an account</Link></>}
    >
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        {state?.notice && <p className="qy-form-note" role="status">{state.notice}</p>}
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field id="password" label="Password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
        <Link className="qy-link" to="/forgot-password" style={{ alignSelf: 'flex-start' }}>Forgot password?</Link>
      </form>
    </AuthCard>
  )
}
