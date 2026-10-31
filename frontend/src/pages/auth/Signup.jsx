import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', website: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/auth/register', { method: 'POST', body: form })
      navigate('/verify', { state: { email: form.email.trim() } })
    } catch (err) {
      setError(err.status === 422
        ? 'Enter your first name, a valid email and a password of at least 8 characters.'
        : errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Create your account"
      intro="We'll email you a code to confirm your address."
      footer={<>Already have an account? <Link className="qy-link" to="/login">Log in</Link></>}
    >
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="first-name" label="First name" autoComplete="given-name" required maxLength={50} value={form.first_name} onChange={set('first_name')} />
        <Field id="last-name" label="Last name (optional)" autoComplete="family-name" maxLength={50} value={form.last_name} onChange={set('last_name')} />
        <Field id="email" label="Email" type="email" autoComplete="email" required value={form.email} onChange={set('email')} />
        <Field id="password" label="Password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} hint="At least 8 characters." value={form.password} onChange={set('password')} />
        <div className="qy-honeypot" aria-hidden="true">
          <label htmlFor="website">Leave this empty</label>
          <input id="website" tabIndex={-1} autoComplete="off" value={form.website} onChange={set('website')} />
        </div>
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Creating…' : 'Sign up'}</button>
      </form>
    </AuthCard>
  )
}
