import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'

export default function ForgotPassword() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/auth/forgot-password', { method: 'POST', body: { email } })
      navigate('/reset-password', { state: { email: email.trim() } })
    } catch (err) {
      setError(err.status === 422 ? 'Enter a valid email address.' : errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <AuthCard
      title="Forgot your password?"
      intro="If the address has an account, we'll email it a code to choose a new password."
      footer={<Link className="qy-link" to="/login">Back to log in</Link>}
    >
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Sending…' : 'Send code'}</button>
      </form>
    </AuthCard>
  )
}
