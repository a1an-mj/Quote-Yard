import { Link } from 'react-router-dom'
import DealCarousel from '../components/DealCarousel'
import Footer from '../components/Footer'
import PublicNav from '../components/PublicNav'
import { formatCount } from '../lib/format'
import { useApi } from '../lib/useApi'

const STEPS = [
  ['01', 'We collect listings', 'Product pages from retailer websites are read every day. Each price keeps the time we saw it.'],
  ['02', 'We match the exact variant', 'Listings are grouped by model and configuration, so an 8 GB / 128 GB phone is never compared with the 256 GB version.'],
  ['03', 'You see every listed price', "Prices are sorted lowest first with stock status and when we last saw them. Buy on the store's own page."],
]

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

function Stat({ value, label }) {
  return (
    <div className="qy-stack" style={{ gap: 2 }}>
      <span className="qy-dotnum" style={{ fontSize: 44 }}>{value ?? '–'}</span>
      <span className="qy-small">{label}</span>
    </div>
  )
}

export default function Landing() {
  const deals = useApi('/public/deals')
  const retailers = useApi('/retailers')
  const stores = retailers.data ?? []
  const listings = stores.reduce((sum, store) => sum + store.listings, 0)

  return (
    <>
      <PublicNav />
      <main>
        <section className="qy-wrap qy-split" style={{ paddingBlock: '72px 56px' }}>
          <div className="qy-stack" style={{ gap: 28, minWidth: 0 }}>
            <p className="qy-label">Price comparison · Kerala</p>
            <h1 className="qy-display qy-hero__title">Every listed price, side by side.</h1>
            <p className="qy-body" style={{ fontSize: 17 }}>
              See what stores across Kerala list a product for, which variant each price belongs
              to, and when we last checked it.
            </p>
            <div className="qy-row" style={{ flexWrap: 'wrap' }}>
              <Link className="qy-btn qy-btn--primary" to="/signup">Sign up free</Link>
              <Link className="qy-btn" to="/login">Log in</Link>
            </div>
          </div>
          <aside className="qy-tile qy-tile--pad qy-stack" style={{ gap: 20 }} aria-label="Coverage">
            <p className="qy-label">Coverage</p>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 20 }}>
              <Stat value={retailers.data ? stores.length : null} label="stores compared" />
              <Stat value={retailers.data ? formatCount(listings) : null} label="listings tracked" />
            </div>
          </aside>
        </section>

        <section id="deals" className="qy-wrap qy-section" aria-labelledby="deals-title" style={{ borderTop: '1px solid var(--qy-line)' }}>
          <div className="qy-between" style={{ marginBottom: 24 }}>
            <div className="qy-stack" style={{ gap: 4 }}>
              <p className="qy-label">Calculated from recorded prices</p>
              <h2 className="qy-h1" id="deals-title">Today's deals</h2>
            </div>
            <p className="qy-small" style={{ maxWidth: '44ch' }}>
              A real recorded price drop, or a clear gap between stores. Never measured against an
              MRP.
            </p>
          </div>
          <DealCarousel deals={deals.data} loading={deals.loading} error={deals.error} onRetry={deals.retry} />
        </section>

        <section id="stores" className="qy-wrap qy-section" aria-labelledby="stores-title" style={{ paddingTop: 0 }}>
          <div className="qy-stack" style={{ gap: 4, marginBottom: 24 }}>
            <p className="qy-label">Retailers</p>
            <h2 className="qy-h1" id="stores-title">Stores we compare</h2>
          </div>
          {retailers.error ? (
            <div className="qy-empty" role="alert">
              <p className="qy-small">We couldn't load the store list.</p>
              <button className="qy-btn" type="button" onClick={retailers.retry}>Try again</button>
            </div>
          ) : (
            <ul className="qy-grid-4" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {stores.map((store) => (
                <li key={store.id} className="qy-tile" style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px' }}>
                  <span className="qy-dotnum" aria-hidden="true" style={{ width: 44, height: 44, flex: 'none', border: '1px solid var(--qy-ink)', borderRadius: '50%', display: 'grid', placeItems: 'center', fontSize: 18 }}>
                    {store.name[0].toUpperCase()}
                  </span>
                  <span className="qy-stack" style={{ gap: 0, minWidth: 0 }}>
                    <span style={{ fontWeight: 500 }}>{store.name}</span>
                    {store.base_url && (
                      <a className="qy-small" href={store.base_url} target="_blank" rel="noopener noreferrer">{hostOf(store.base_url)}</a>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section id="how" className="qy-wrap qy-section" aria-labelledby="how-title" style={{ paddingTop: 0 }}>
          <div className="qy-between" style={{ marginBottom: 32 }}>
            <h2 className="qy-h1" id="how-title">How price comparison works</h2>
            <p className="qy-small" style={{ maxWidth: '44ch' }}>
              We only show prices a store has published. Savings compare prices we recorded, and we
              never estimate a price we don't have.
            </p>
          </div>
          <ol className="qy-grid-3" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
            {STEPS.map(([number, title, body]) => (
              <li key={number} className="qy-tile qy-tile--pad qy-stack" style={{ gap: 14 }}>
                <span className="qy-dotnum" style={{ fontSize: 40 }}>{number}</span>
                <h3 className="qy-h3">{title}</h3>
                <p className="qy-small">{body}</p>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <Footer />
    </>
  )
}
