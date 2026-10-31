import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'
import { useAuth } from '../../lib/auth'

export default function ResetPassword() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const { setUser } = useAuth()
  const [form, setForm] = useState({ email: state?.email ?? '', code: '', new_password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/auth/reset-password', { method: 'POST', body: form })
      setUser(null) // a new password ends every session
      navigate('/login', { replace: true, state: { email: form.email, notice: 'Password changed. Log in with the new one.' } })
    } catch (err) {
      setError(err.status === 422
        ? 'Enter the 6-digit code and a password of at least 8 characters.'
        : errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Choose a new password"
      intro="Enter the code from the email. A new password logs you out everywhere."
      footer={<Link className="qy-link" to="/forgot-password">Didn't get a code?</Link>}
    >
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="email" label="Email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        <Field id="code" label="Code" className="qy-input qy-input--code" inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} value={form.code} onChange={set('code')} />
        <Field id="new-password" label="New password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} hint="At least 8 characters." value={form.new_password} onChange={set('new_password')} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Saving…' : 'Change password'}</button>
      </form>
    </AuthCard>
  )
}
