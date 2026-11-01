export default function ErrorBlock({ what, onRetry }) {
  return (
    <div className="qy-empty" role="alert">
      <h3 className="qy-h3">We couldn't load {what}</h3>
      <p className="qy-small">Our server didn't respond. Nothing has been changed.</p>
      <button className="qy-btn" type="button" onClick={onRetry}>Try again</button>
    </div>
  )
}
