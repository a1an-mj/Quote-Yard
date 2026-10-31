import { Link } from 'react-router-dom'
import Footer from '../components/Footer'
import PublicNav from '../components/PublicNav'

export default function NotFound() {
  return (
    <>
      <PublicNav />
      <main className="qy-wrap qy-section">
        <div className="qy-empty">
          <h1 className="qy-h1">Page not found</h1>
          <p className="qy-small">That page doesn't exist or isn't available yet.</p>
          <Link className="qy-btn" to="/">Back to Quote Yard</Link>
        </div>
      </main>
      <Footer />
    </>
  )
}
