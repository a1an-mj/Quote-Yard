import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'
import { useAuth } from '../../lib/auth'

const COOLDOWN_S = 60

export default function Verify() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const { setUser } = useAuth()
  const [email, setEmail] = useState(state?.email ?? '')
  const [code, setCode] = useState('')
  const [error, setError] = useState(null)
  const [note, setNote] = useState(null)
  const [busy, setBusy] = useState(false)
  const [wait, setWait] = useState(COOLDOWN_S)

  useEffect(() => {
    if (wait <= 0) return undefined
    const timer = setTimeout(() => setWait(wait - 1), 1000)
    return () => clearTimeout(timer)
  }, [wait])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setNote(null)
    try {
      setUser(await api('/auth/verify-email', { method: 'POST', body: { email, code } }))
      navigate('/home', { replace: true })
    } catch (err) {
      setError(err.status === 422 ? 'Enter the 6-digit code from the email.' : errorMessage(err))
      setBusy(false)
    }
  }

  async function resend() {
    setError(null)
    try {
      await api('/auth/resend-code', { method: 'POST', body: { email } })
      setNote('If that address is waiting for a code, a new one is on its way.')
      setWait(COOLDOWN_S)
    } catch (err) {
      setError(err.status === 422 ? 'Enter your email first.' : errorMessage(err))
    }
  }

  return (
    <AuthCard title="Check your email" intro="Enter the 6-digit code we sent you. It works for 10 minutes.">
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field id="code" label="Code" className="qy-input qy-input--code" inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        {note && <p className="qy-form-note" role="status">{note}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Checking…' : 'Confirm email'}</button>
        <button className="qy-btn qy-btn--quiet" type="button" disabled={wait > 0} onClick={resend}>
          {wait > 0 ? `Send a new code in ${wait}s` : 'Send a new code'}
        </button>
      </form>
    </AuthCard>
  )
}
