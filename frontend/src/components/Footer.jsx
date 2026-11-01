import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="qy-foot">
      <div className="qy-wrap qy-stack" style={{ gap: 10 }}>
        <span className="qy-logo" style={{ fontSize: 18 }}>Quote Yard</span>
        <p className="qy-small" style={{ maxWidth: '60ch' }}>
          Listed prices from Kerala retailers. Prices and stock change often; always confirm on
          the store's page before you buy.
        </p>
        <Link className="qy-small" to="/vendor/login">Shop owners: log in</Link>
      </div>
    </footer>
  )
}
