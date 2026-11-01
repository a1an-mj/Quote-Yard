import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatPrice } from '../lib/format'
import { useApi } from '../lib/useApi'

export default function ProductActions({ productId, lowest }) {
  const { user } = useAuth()
  const saved = useApi('/me/saved')
  const alerts = useApi('/me/alerts')
  const [open, setOpen] = useState(false)
  const [target, setTarget] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const isSaved = saved.data?.some((item) => item.product.id === productId)
  const alert = alerts.data?.find((item) => item.product.id === productId)
  const loading = saved.loading || alerts.loading
  const amount = Number(target)
  const valid = Number.isInteger(amount) && amount > 0

  async function run(action) {
    setBusy(true)
    setError(null)
    try {
      await action()
      return true
    } catch (err) {
      setError(errorMessage(err))
      return false
    } finally {
      setBusy(false)
    }
  }

  const toggleSave = () =>
    run(async () => {
      await api(`/me/saved/${productId}`, { method: isSaved ? 'DELETE' : 'PUT' })
      saved.retry()
    })

  function openForm() {
    setTarget(alert ? String(alert.target_price) : '')
    setError(null)
    setOpen(true)
  }

  async function saveAlert(e) {
    e.preventDefault()
    if (!valid) {
      setError('Enter a whole rupee amount above zero.')
      return
    }
    const ok = await run(async () => {
      await api(`/me/alerts/${productId}`, { method: 'PUT', body: { target_price: amount } })
      alerts.retry()
    })
    if (ok) setOpen(false)
  }

  async function removeAlert() {
    const ok = await run(async () => {
      await api(`/me/alerts/${productId}`, { method: 'DELETE' })
      alerts.retry()
    })
    if (ok) setOpen(false)
  }

  return (
    <div className="qy-stack" style={{ gap: 12 }}>
      <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
        <button className={`qy-btn ${isSaved ? '' : 'qy-btn--quiet'}`} type="button" disabled={busy || loading} aria-pressed={Boolean(isSaved)} onClick={toggleSave}>
          {isSaved ? 'Saved ✓' : 'Save'}
        </button>
        <button className="qy-btn qy-btn--quiet" type="button" disabled={busy || loading} aria-expanded={open} onClick={() => (open ? setOpen(false) : openForm())}>
          {alert ? `Alert below ${formatPrice(alert.target_price)}` : 'Set price alert'}
        </button>
        <Link className="qy-link" to="/saved">Your saved items</Link>
      </div>
      {open && (
        <form className="qy-tile qy-tile--pad qy-stack" style={{ gap: 12, maxWidth: 460 }} onSubmit={saveAlert}>
          <div className="qy-field">
            <label className="qy-small" htmlFor="alert-target" style={{ color: 'var(--qy-ink)' }}>Email me when the lowest price goes below (₹)</label>
            <input id="alert-target" className="qy-input qy-num" type="number" inputMode="numeric" min="1" step="1" required autoFocus value={target} onChange={(e) => { setTarget(e.target.value); setError(null) }} />
          </div>
          <p className="qy-small">
            We check prices once a day and email {user.email}.
            {lowest != null && <> The lowest now is {formatPrice(lowest)}.</>}
            {valid && lowest != null && lowest < amount && <> That's already below {formatPrice(amount)}, so you'd hear from us after the next check.</>}
          </p>
          <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
            <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>Save alert</button>
            <button className="qy-btn qy-btn--ghost" type="button" onClick={() => setOpen(false)}>Cancel</button>
            {alert && <button className="qy-btn qy-btn--ghost" type="button" disabled={busy} onClick={removeAlert}>Remove alert</button>}
          </div>
        </form>
      )}
      {(error || saved.error || alerts.error) && (
        <p className="qy-form-error" role="alert">{error ?? "We couldn't load your saved items and alerts."}</p>
      )}
    </div>
  )
}
