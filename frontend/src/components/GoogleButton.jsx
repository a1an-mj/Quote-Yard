import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'

const SCRIPT = 'https://accounts.google.com/gsi/client'
let scriptLoad = null // one copy of Google's script for the whole site

function loadScript() {
  scriptLoad ??= new Promise((resolve, reject) => {
    const tag = document.createElement('script')
    tag.src = SCRIPT
    tag.async = true
    tag.onload = resolve
    tag.onerror = () => { scriptLoad = null; reject(new Error('Google script failed')) }
    document.head.appendChild(tag)
  })
  return scriptLoad
}

// "Continue with Google". Shows nothing until the server has a Google client ID.
export default function GoogleButton({ text = 'continue_with' }) {
  const box = useRef(null)
  const navigate = useNavigate()
  const { state } = useLocation()
  const { setUser } = useAuth()
  const [clientId, setClientId] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    api('/auth/google-config').then((c) => live && setClientId(c.client_id)).catch(() => {})
    return () => { live = false }
  }, [])

  useEffect(() => {
    if (!clientId) return
    let live = true
    loadScript().then(() => {
      if (!live || !box.current) return
      const google = window.google.accounts.id
      google.initialize({
        client_id: clientId,
        ux_mode: 'popup',
        callback: async ({ credential }) => {
          setBusy(true)
          setError(null)
          try {
            setUser(await api('/auth/google', { method: 'POST', body: { credential } }))
            navigate(state?.from ?? '/home', { replace: true })
          } catch (err) {
            setError(errorMessage(err))
            setBusy(false)
          }
        },
      })
      const dark = document.documentElement.classList.contains('qy--dark')
      google.renderButton(box.current, {
        type: 'standard', shape: 'pill', size: 'large', text,
        theme: dark ? 'filled_black' : 'outline',
        width: Math.min(box.current.offsetWidth || 320, 400),
      })
    }).catch(() => live && setError("Google sign-in couldn't load. Use your email instead."))
    return () => { live = false }
  }, [clientId, text, navigate, setUser, state])

  if (!clientId) return null
  return (
    <div className="qy-stack qy-google" style={{ gap: 12 }} aria-busy={busy}>
      <div ref={box} className="qy-google__button" />
      {error && <p className="qy-form-error" role="alert">{error}</p>}
      <p className="qy-google__or qy-small"><span>or use your email</span></p>
    </div>
  )
}
