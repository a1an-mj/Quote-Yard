import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthCard from '../../components/AuthCard'
import Field from '../../components/Field'
import { api, errorMessage } from '../../lib/api'

const DISTRICTS = ['Alappuzha', 'Ernakulam', 'Idukki', 'Kannur', 'Kasaragod', 'Kollam', 'Kottayam', 'Kozhikode', 'Malappuram', 'Palakkad', 'Pathanamthitta', 'Thiruvananthapuram', 'Thrissur', 'Wayanad']

// Emailed links carry the token after the #, so it never reaches the server's logs.
function useLinkToken() {
  return useLocation().hash.slice(1)
}

function useSubmit(action) {
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  return { error, busy, submit }
}

export function VendorLogin() {
  const navigate = useNavigate()
  const { state } = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { error, busy, submit } = useSubmit(async () => {
    await api('/vendor/login', { method: 'POST', body: { email, password } })
    navigate('/vendor', { replace: true })
  })
  return (
    <AuthCard title="Shop login" intro="For local shops listing offers on Quote Yard. Joining is by invite." footer={<>Looking for prices? <Link className="qy-link" to="/login">Customer login</Link></>}>
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        {state?.notice && <p className="qy-form-note" role="status">{state.notice}</p>}
        <Field id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <Field id="password" label="Password" type="password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
        <Link className="qy-link" to="/vendor/forgot-password" style={{ alignSelf: 'flex-start' }}>Forgot password?</Link>
      </form>
    </AuthCard>
  )
}

export function VendorJoin() {
  const token = useLinkToken()
  const navigate = useNavigate()
  const [form, setForm] = useState({ shop_name: '', owner_name: '', phone: '', address: '', town: '', district: '', gst_number: '', password: '' })
  const set = (name) => (e) => setForm({ ...form, [name]: e.target.value })
  const { error, busy, submit } = useSubmit(async () => {
    await api('/vendor/join', { method: 'POST', body: { ...form, token, gst_number: form.gst_number || null } })
    navigate('/vendor', { replace: true })
  })
  return (
    <AuthCard title="Set up your shop" intro="We review these details before your offers can appear. Customers will see your shop name, town, district, phone number and a map link.">
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="shop" label="Shop name" required maxLength={80} value={form.shop_name} onChange={set('shop_name')} />
        <Field id="owner" label="Your name" autoComplete="name" required maxLength={80} value={form.owner_name} onChange={set('owner_name')} />
        <Field id="phone" label="Shop phone number" type="tel" autoComplete="tel" required value={form.phone} onChange={set('phone')} />
        <Field id="address" label="Shop address" required maxLength={200} value={form.address} onChange={set('address')} />
        <Field id="town" label="Town" required maxLength={60} value={form.town} onChange={set('town')} />
        <div className="qy-field">
          <label className="qy-small" htmlFor="district" style={{ color: 'var(--qy-ink)' }}>District</label>
          <select className="qy-input" id="district" required value={form.district} onChange={set('district')}>
            <option value="">Choose a district</option>
            {DISTRICTS.map((d) => <option key={d}>{d}</option>)}
          </select>
        </div>
        <Field id="gst" label="GST number (optional)" hint="Only used for the review. Customers never see it." maxLength={15} value={form.gst_number} onChange={set('gst_number')} />
        <Field id="password" label="Password" type="password" autoComplete="new-password" hint="At least 8 characters." required minLength={8} maxLength={128} value={form.password} onChange={set('password')} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy || !token}>{busy ? 'Sending…' : 'Send for review'}</button>
        {!token && <p className="qy-form-error" role="alert">Please open the full link from your invite email.</p>}
      </form>
    </AuthCard>
  )
}

export function VendorForgot() {
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)
  const { error, busy, submit } = useSubmit(async () => {
    await api('/vendor/forgot-password', { method: 'POST', body: { email } })
    setDone(true)
  })
  return (
    <AuthCard title="Reset your shop password" footer={<Link className="qy-link" to="/vendor/login">Back to shop login</Link>}>
      {done ? <p className="qy-form-note" role="status">If that address has a shop, a link is on its way. It expires in 1 hour.</p> : (
        <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
          <Field id="email" label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          {error && <p className="qy-form-error" role="alert">{error}</p>}
          <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>Email me a link</button>
        </form>
      )}
    </AuthCard>
  )
}

export function VendorReset() {
  const token = useLinkToken()
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const { error, busy, submit } = useSubmit(async () => {
    await api('/vendor/reset-password', { method: 'POST', body: { token, new_password: password } })
    navigate('/vendor/login', { replace: true, state: { notice: 'Password changed. Log in with the new one.' } })
  })
  return (
    <AuthCard title="Choose a new password">
      <form className="qy-stack" style={{ gap: 16 }} onSubmit={submit}>
        <Field id="password" label="New password" type="password" autoComplete="new-password" hint="At least 8 characters." required minLength={8} maxLength={128} value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <p className="qy-form-error" role="alert">{error}</p>}
        <button className="qy-btn qy-btn--primary" type="submit" disabled={busy || !token}>Change password</button>
      </form>
    </AuthCard>
  )
}
