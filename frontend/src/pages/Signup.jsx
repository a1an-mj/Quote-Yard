import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Tag, ArrowRight } from 'lucide-react'
import Button from '../components/Button'
import GoogleButton from '../components/GoogleButton'
import FormField, { inputClasses } from '../components/FormField'
import { useAuth } from '../context/AuthContext'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^[6-9]\d{9}$/

export default function Signup() {
  const { signup, loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    fullName: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: '',
  })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function validate() {
    const e = {}
    if (!form.fullName.trim()) e.fullName = 'Tell us your name so we can greet you properly.'
    if (!form.email.trim()) e.email = 'We need an email to create your account.'
    else if (!EMAIL_RE.test(form.email)) e.email = 'That email doesn\u2019t look quite right.'
    if (!form.phone.trim()) e.phone = 'A phone number helps us send price alerts.'
    else if (!PHONE_RE.test(form.phone.replace(/\D/g, ''))) e.phone = 'Enter a valid 10-digit Indian mobile number.'
    if (!form.password) e.password = 'Choose a password to secure your account.'
    else if (form.password.length < 6) e.password = 'Use at least 6 characters.'
    if (form.confirmPassword !== form.password) e.confirmPassword = 'Passwords don\u2019t match yet.'
    return e
  }

  function handleSubmit(ev) {
    ev.preventDefault()
    const foundErrors = validate()
    setErrors(foundErrors)
    if (Object.keys(foundErrors).length > 0) return

    setSubmitting(true)
    // Simulated registration — no real backend is involved in this prototype.
    setTimeout(() => {
      signup({ fullName: form.fullName.trim(), email: form.email.trim() })
      navigate('/dashboard')
    }, 500)
  }

  function handleGoogle() {
    loginWithGoogle()
    navigate('/dashboard')
  }

  return (
    <div className="flex min-h-screen flex-col bg-ivory lg:flex-row">
      {/* Brand panel */}
      <div className="hidden w-full flex-col justify-between bg-ink p-12 text-ivory lg:flex lg:w-2/5">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-ivory bg-terracotta">
            <Tag size={18} strokeWidth={2.5} />
          </span>
          <span className="font-display text-lg font-bold">Quote Yard</span>
        </Link>
        <div>
          <p className="font-display text-3xl font-bold leading-tight">
            Join thousands of shoppers finding the better price, every time.
          </p>
          <p className="mt-4 font-body text-ivory/60">
            It takes less than a minute &mdash; and you'll never wonder if you overpaid again.
          </p>
        </div>
        <p className="font-body text-xs text-ivory/40">A Quote Yard prototype &middot; mock data only</p>
      </div>

      {/* Form panel */}
      <div className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6 lg:px-12">
        <div className="w-full max-w-md">
          <Link to="/" className="mb-8 flex items-center gap-2 lg:hidden">
            <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-ink bg-terracotta text-ivory">
              <Tag size={18} strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold text-ink">Quote Yard</span>
          </Link>

          <h1 className="font-display text-3xl font-bold text-ink">Create your Quote Yard account</h1>
          <p className="mt-2 font-body text-sm text-walnut">Start comparing prices in under a minute.</p>

          <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-4">
            <FormField label="Full Name" error={errors.fullName}>
              <input
                type="text"
                value={form.fullName}
                onChange={(e) => update('fullName', e.target.value)}
                placeholder="Anjali Menon"
                className={inputClasses(errors.fullName)}
              />
            </FormField>

            <FormField label="Email" error={errors.email}>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="anjali@example.com"
                className={inputClasses(errors.email)}
              />
            </FormField>

            <FormField label="Phone Number" error={errors.phone}>
              <input
                type="tel"
                value={form.phone}
                onChange={(e) => update('phone', e.target.value)}
                placeholder="98765 43210"
                className={inputClasses(errors.phone)}
              />
            </FormField>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <FormField label="Password" error={errors.password}>
                <input
                  type="password"
                  value={form.password}
                  onChange={(e) => update('password', e.target.value)}
                  placeholder="••••••••"
                  className={inputClasses(errors.password)}
                />
              </FormField>
              <FormField label="Confirm Password" error={errors.confirmPassword}>
                <input
                  type="password"
                  value={form.confirmPassword}
                  onChange={(e) => update('confirmPassword', e.target.value)}
                  placeholder="••••••••"
                  className={inputClasses(errors.confirmPassword)}
                />
              </FormField>
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={submitting}>
              {submitting ? 'Creating account…' : 'Create Account'}
              {!submitting && <ArrowRight size={18} />}
            </Button>
          </form>

          <div className="my-6 flex items-center gap-3">
            <div className="h-px flex-1 bg-ink/15" />
            <span className="font-body text-xs font-semibold uppercase tracking-wide text-walnut/50">or</span>
            <div className="h-px flex-1 bg-ink/15" />
          </div>

          <GoogleButton onClick={handleGoogle} />

          <p className="mt-6 text-center font-body text-sm text-walnut">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-terracotta hover:underline">
              Login
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
