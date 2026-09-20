import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Tag, ArrowRight } from 'lucide-react'
import Button from '../components/Button'
import GoogleButton from '../components/GoogleButton'
import FormField, { inputClasses } from '../components/FormField'
import { useAuth } from '../context/AuthContext'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function Login() {
  const { login, loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function validate() {
    const e = {}
    if (!form.email.trim()) e.email = 'Enter the email you signed up with.'
    else if (!EMAIL_RE.test(form.email)) e.email = 'That email doesn\u2019t look quite right.'
    if (!form.password) e.password = 'Enter your password to continue.'
    return e
  }

  function handleSubmit(ev) {
    ev.preventDefault()
    const foundErrors = validate()
    setErrors(foundErrors)
    if (Object.keys(foundErrors).length > 0) return

    setSubmitting(true)
    // Mock authentication — any valid-looking email/password combination succeeds.
    setTimeout(() => {
      login({ email: form.email.trim() })
      navigate('/dashboard')
    }, 400)
  }

  function handleGoogle() {
    loginWithGoogle()
    navigate('/dashboard')
  }

  return (
    <div className="flex min-h-screen flex-col bg-ivory lg:flex-row">
      <div className="hidden w-full flex-col justify-between bg-olive p-12 text-ivory lg:flex lg:w-2/5">
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-ivory bg-terracotta">
            <Tag size={18} strokeWidth={2.5} />
          </span>
          <span className="font-display text-lg font-bold">Quote Yard</span>
        </Link>
        <div>
          <p className="font-display text-3xl font-bold leading-tight">
            Welcome back. Your best price is waiting.
          </p>
          <p className="mt-4 font-body text-ivory/70">
            Pick up right where you left off comparing.
          </p>
        </div>
        <p className="font-body text-xs text-ivory/40">A Quote Yard prototype &middot; mock data only</p>
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-10 sm:px-6 lg:px-12">
        <div className="w-full max-w-md">
          <Link to="/" className="mb-8 flex items-center gap-2 lg:hidden">
            <span className="flex h-9 w-9 items-center justify-center rounded-full border-2 border-ink bg-terracotta text-ivory">
              <Tag size={18} strokeWidth={2.5} />
            </span>
            <span className="font-display text-lg font-bold text-ink">Quote Yard</span>
          </Link>

          <h1 className="font-display text-3xl font-bold text-ink">Login to Quote Yard</h1>
          <p className="mt-2 font-body text-sm text-walnut">
            This is a prototype &mdash; any valid-looking email and password will work.
          </p>

          <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-4">
            <FormField label="Email" error={errors.email}>
              <input
                type="email"
                value={form.email}
                onChange={(e) => update('email', e.target.value)}
                placeholder="anjali@example.com"
                className={inputClasses(errors.email)}
              />
            </FormField>

            <FormField label="Password" error={errors.password}>
              <input
                type="password"
                value={form.password}
                onChange={(e) => update('password', e.target.value)}
                placeholder="••••••••"
                className={inputClasses(errors.password)}
              />
            </FormField>

            <div className="text-right">
              <Link to="#" onClick={(e) => e.preventDefault()} className="font-body text-sm font-semibold text-terracotta hover:underline">
                Forgot password?
              </Link>
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={submitting}>
              {submitting ? 'Logging in…' : 'Login'}
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
            Don't have an account?{' '}
            <Link to="/signup" className="font-semibold text-terracotta hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
