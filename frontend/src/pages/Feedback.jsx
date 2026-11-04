import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, Send } from 'lucide-react'
import Footer from '../components/Footer'
import PublicNav from '../components/PublicNav'
import { api, errorMessage } from '../lib/api'

// The highlight colours testers can try. Keys match api/routes/feedback.py.
const COLOURS = [
  { key: 'neon-green', name: 'Neon green', hex: '#4DFF00', on: '#141414', note: 'Before' },
  { key: 'sunflower', name: 'Sunflower', hex: '#FFD23F', on: '#141414' },
  { key: 'coral', name: 'Coral', hex: '#FF8A65', on: '#141414', note: 'Now' },
  { key: 'sky', name: 'Sky', hex: '#6CC4FF', on: '#141414' },
  { key: 'lavender', name: 'Lavender', hex: '#B9A4FF', on: '#141414' },
  { key: 'ink', name: 'Ink', hex: 'var(--qy-ink)', on: 'var(--qy-surface)', label: 'Black (white in dark mode)' },
]
const FATIGUE = [['not-at-all', 'Not at all'], ['a-little', 'A little'], ['quite', 'Quite tiring'], ['very', 'Very tiring']]
const DEVICES = [['phone', 'Phone'], ['computer', 'Computer'], ['tablet', 'Tablet']]
const EMPTY = {
  rating: '', colour: '', colour_note: '', fatigue: '', fatigue_note: '', problems: '', mistakes: '',
  questions: '', suggestions: '', device: '', name: '', email: '', website: '',
}

function Question({ n, title, hint, children }) {
  return (
    <fieldset className="qy-fb__q">
      <legend className="qy-fb__legend"><span className="qy-dotnum qy-fb__n">0{n}</span>{title}</legend>
      {hint && <p className="qy-small">{hint}</p>}
      {children}
    </fieldset>
  )
}

function Pills({ name, options, value, onChange }) {
  return (
    <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
      {options.map(([key, label]) => (
        <label key={key} className="qy-pick">
          <input type="radio" name={name} value={key} checked={value === key} onChange={() => onChange(key)} />
          {label}
        </label>
      ))}
    </div>
  )
}

function Box({ id, label, value, onChange, rows = 3, placeholder }) {
  return (
    <div className="qy-field">
      <label className="qy-small" htmlFor={id} style={{ color: 'var(--qy-ink)' }}>{label}</label>
      <textarea id={id} className="qy-input qy-fb__text" rows={rows} maxLength={2000} placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} />
    </div>
  )
}

export default function Feedback() {
  const [form, setForm] = useState(EMPTY)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [sent, setSent] = useState(false)
  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }))
  const picked = COLOURS.find((c) => c.key === form.colour)
  // The chosen colour is tried on this whole page, header buttons included.
  const tryOn = picked ? { '--qy-cta': picked.hex, '--qy-on-cta': picked.on } : undefined

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/public/feedback', { method: 'POST', body: { ...form, rating: form.rating ? Number(form.rating) : null } })
      setSent(true)
      window.scrollTo({ top: 0 })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={tryOn}>
      <PublicNav />
      <main className="qy-wrap" style={{ paddingBlock: '40px 72px' }}>
        {sent ? (
          <div className="qy-fb qy-tile qy-tile--pad qy-stack qy-fb__done" role="status">
            <span className="qy-ticon qy-ticon--lg qy-hue--teal" aria-hidden="true"><Check strokeWidth={1.8} /></span>
            <h1 className="qy-h1">Thank you!</h1>
            <p className="qy-body">Your feedback went straight to the Quote Yard team. It really helps.</p>
            <div className="qy-row" style={{ gap: 8, flexWrap: 'wrap' }}>
              <Link className="qy-btn qy-btn--primary" to="/">Back to Quote Yard</Link>
              <button className="qy-btn" type="button" onClick={() => { setForm(EMPTY); setSent(false) }}>Send more</button>
            </div>
          </div>
        ) : (
          <form className="qy-fb qy-stack" style={{ gap: 28 }} onSubmit={submit}>
            <div className="qy-stack" style={{ gap: 10 }}>
              <p className="qy-label">Preview · help us improve</p>
              <h1 className="qy-h1">Tell us what you think</h1>
              <p className="qy-body" style={{ fontSize: 17 }}>Quote Yard isn't finished yet. Answer as many or as few questions as you like; every answer is read.</p>
            </div>

            <Question n={1} title="Overall, how would you rate Quote Yard?" hint="1 is poor, 10 is excellent.">
              <div className="qy-fb__rating" role="radiogroup" aria-label="Rating out of 10">
                {Array.from({ length: 10 }, (_, i) => String(i + 1)).map((n) => (
                  <label key={n} className="qy-pick">
                    <input type="radio" name="rating" value={n} checked={form.rating === n} onChange={() => set('rating')(n)} aria-label={`${n} out of 10`} />
                    {n}
                  </label>
                ))}
              </div>
            </Question>

            <Question n={2} title="The highlight colour" hint="The bright colour on main buttons like Sign up and Search. Tap one to try it on this page.">
              <div className="qy-fb__swatches" role="radiogroup" aria-label="Highlight colour">
                {COLOURS.map((c) => (
                  <label key={c.key} className="qy-swatch">
                    <input type="radio" name="colour" value={c.key} checked={form.colour === c.key} onChange={() => set('colour')(c.key)} />
                    <span className="qy-swatch__sample" style={{ background: c.hex, color: c.on }}>Sign up</span>
                    <span className="qy-swatch__name">{c.name}{c.note && <span className="qy-badge" style={{ marginLeft: 6 }}>{c.note}</span>}</span>
                    <span className="qy-small">{c.label ?? c.hex}</span>
                  </label>
                ))}
                <label className="qy-swatch qy-swatch--other">
                  <input type="radio" name="colour" value="other" checked={form.colour === 'other'} onChange={() => set('colour')('other')} />
                  <span className="qy-swatch__sample qy-swatch__sample--other">?</span>
                  <span className="qy-swatch__name">Something else</span>
                  <span className="qy-small">Tell us below</span>
                </label>
              </div>
              <p className="qy-small">Green marks the lowest price everywhere on the site, so the highlight should stay clearly different from it.</p>
              <div className="qy-field">
                <label className="qy-small" htmlFor="colour-note" style={{ color: 'var(--qy-ink)' }}>Why, or which other colour? (optional)</label>
                <input id="colour-note" className="qy-input" maxLength={300} value={form.colour_note} onChange={(e) => set('colour_note')(e.target.value)} />
              </div>
            </Question>

            <Question n={3} title="Does the site feel tiring to look at?">
              <Pills name="fatigue" options={FATIGUE} value={form.fatigue} onChange={set('fatigue')} />
              <Box id="fatigue-note" label="What felt tiring, or what felt good? (optional)" value={form.fatigue_note} onChange={set('fatigue_note')} rows={2} />
            </Question>

            <Question n={4} title="Did anything go wrong?" hint="Something that didn't work, was confusing, slow, or looked broken. Which page, and what did you do?">
              <Box id="problems" label="Problems" value={form.problems} onChange={set('problems')} />
            </Question>

            <Question n={5} title="Spelling mistakes or wrong details?" hint="A typo, a wrong price or product name, or wrong store information.">
              <Box id="mistakes" label="Mistakes" value={form.mistakes} onChange={set('mistakes')} />
            </Question>

            <Question n={6} title="Anything you want to ask?">
              <Box id="questions" label="Your questions" value={form.questions} onChange={set('questions')} />
            </Question>

            <Question n={7} title="Any other ideas?" hint="Stores, features, or anything you'd change.">
              <Box id="suggestions" label="Suggestions" value={form.suggestions} onChange={set('suggestions')} />
            </Question>

            <Question n={8} title="About you (optional)">
              <p className="qy-small">What did you use?</p>
              <Pills name="device" options={DEVICES} value={form.device} onChange={set('device')} />
              <div className="qy-fb__who">
                <div className="qy-field">
                  <label className="qy-small" htmlFor="fb-name" style={{ color: 'var(--qy-ink)' }}>Name</label>
                  <input id="fb-name" className="qy-input" autoComplete="name" maxLength={80} value={form.name} onChange={(e) => set('name')(e.target.value)} />
                </div>
                <div className="qy-field">
                  <label className="qy-small" htmlFor="fb-email" style={{ color: 'var(--qy-ink)' }}>Email, if you'd like a reply</label>
                  <input id="fb-email" className="qy-input" type="email" autoComplete="email" maxLength={254} value={form.email} onChange={(e) => set('email')(e.target.value)} />
                </div>
              </div>
            </Question>

            <div className="qy-honeypot" aria-hidden="true">
              <label htmlFor="fb-website">Leave this empty</label>
              <input id="fb-website" tabIndex={-1} autoComplete="off" value={form.website} onChange={(e) => set('website')(e.target.value)} />
            </div>

            {error && <p className="qy-form-error" role="alert">{error}</p>}
            <div className="qy-stack" style={{ gap: 10 }}>
              <button className="qy-btn qy-btn--primary qy-fb__send" type="submit" disabled={busy}>
                <Send size={16} aria-hidden="true" /> {busy ? 'Sending…' : 'Send feedback'}
              </button>
              <p className="qy-small">Your answers are emailed to the Quote Yard team and used only to improve the site. <Link className="qy-link" to="/privacy">Privacy policy</Link></p>
            </div>
          </form>
        )}
      </main>
      <Footer />
    </div>
  )
}
