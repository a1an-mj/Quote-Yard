import { Link } from 'react-router-dom'
import AppNav from '../components/AppNav'
import DealCarousel from '../components/DealCarousel'
import ErrorBlock from '../components/ErrorBlock'
import Footer from '../components/Footer'
import ProductCard, { CardSkeletons } from '../components/ProductCard'
import SearchBox from '../components/SearchBox'
import { useAuth } from '../lib/auth'
import { formatCount } from '../lib/format'
import { useApi } from '../lib/useApi'

function ProductRow({ title, label, link, state }) {
  return (
    <section className="qy-wrap qy-section" style={{ paddingTop: 0 }}>
      <div className="qy-between" style={{ marginBottom: 24 }}>
        <div className="qy-stack" style={{ gap: 4 }}>
          <p className="qy-label">{label}</p>
          <h2 className="qy-h2">{title}</h2>
        </div>
        <Link className="qy-link" to={link}>See more</Link>
      </div>
      {state.error ? (
        <ErrorBlock what={title.toLowerCase()} onRetry={state.retry} />
      ) : (
        <div className="qy-grid-4">
          {state.loading && !state.data
            ? <CardSkeletons />
            : state.data?.items.map((product) => <ProductCard key={product.id} product={product} />)}
        </div>
      )}
    </section>
  )
}

export default function Home() {
  const { user } = useAuth()
  const deals = useApi('/public/deals')
  const compared = useApi('/products?sort=retailers&min_retailers=2&limit=4')
  const newest = useApi('/products?sort=newest&limit=4')
  const types = useApi('/product-types')
  const topTypes = [...(types.data ?? [])].sort((a, b) => b.listings - a.listings).slice(0, 10)

  return (
    <>
      <AppNav search={false} />
      <main>
        <section className="qy-wrap qy-stack" style={{ paddingBlock: '56px', gap: 20 }}>
          <p className="qy-label">Hi {user.first_name}</p>
          <h1 className="qy-display qy-hero__title">What are you buying?</h1>
          <SearchBox />
        </section>

        <section className="qy-wrap qy-section" aria-labelledby="types-title" style={{ paddingTop: 0 }}>
          <h2 className="qy-h2" id="types-title" style={{ marginBottom: 16 }}>Browse by type</h2>
          {types.error ? (
            <ErrorBlock what="product types" onRetry={types.retry} />
          ) : (
            <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
              {topTypes.map((type) => (
                <Link key={type.product_type} className="qy-chip" to={`/search?product_type=${encodeURIComponent(type.product_type)}`}>
                  {type.product_type} <span className="qy-num qy-small">{formatCount(type.listings)}</span>
                </Link>
              ))}
            </div>
          )}
        </section>

        <section className="qy-wrap qy-section" aria-labelledby="deals-title" style={{ paddingTop: 0 }}>
          <div className="qy-stack" style={{ gap: 4, marginBottom: 24 }}>
            <p className="qy-label">Calculated from recorded prices</p>
            <h2 className="qy-h2" id="deals-title">Today's deals</h2>
          </div>
          <DealCarousel deals={deals.data} loading={deals.loading} error={deals.error} onRetry={deals.retry} linked />
        </section>

        <ProductRow title="Most stores compared" label="Matched across retailers" link="/search?min_retailers=2&sort=retailers" state={compared} />
        <ProductRow title="Recently added" label="New in our data" link="/search?sort=newest" state={newest} />
      </main>
      <Footer />
    </>
  )
}
