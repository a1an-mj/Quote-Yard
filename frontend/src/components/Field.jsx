export default function Field({ label, hint, ...input }) {
  const hintId = hint ? `${input.id}-hint` : undefined
  return (
    <div className="qy-field">
      <label className="qy-small" htmlFor={input.id} style={{ color: 'var(--qy-ink)' }}>{label}</label>
      <input className="qy-input" aria-describedby={hintId} {...input} />
      {hint && <span className="qy-small" id={hintId}>{hint}</span>}
    </div>
  )
}
