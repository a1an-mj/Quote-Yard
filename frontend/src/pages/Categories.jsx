import { Link } from 'react-router-dom'
import AppNav, { Breadcrumb } from '../components/AppNav'
import ErrorBlock from '../components/ErrorBlock'
import Footer from '../components/Footer'
import { formatCount } from '../lib/format'
import { useApi } from '../lib/useApi'

const searchBy = (key, value) => `/search?${key}=${encodeURIComponent(value)}`

function CategoryTile({ category, types }) {
  return (
    <li className="qy-tile qy-tile--pad qy-stack" style={{ gap: 14 }}>
      <div className="qy-between" style={{ alignItems: 'baseline' }}>
        <h2 className="qy-h3" style={{ fontSize: 20 }}>{category.category}</h2>
        <span className="qy-label">{formatCount(category.listings)} listings</span>
      </div>
      {types.length > 0 && (
        <ul className="qy-row" style={{ flexWrap: 'wrap', gap: 8, listStyle: 'none', margin: 0, padding: 0 }}>
          {types.map((type) => (
            <li key={type.product_type}>
              <Link className="qy-chip" to={searchBy('product_type', type.product_type)}>
                {type.product_type} <span className="qy-num qy-small">{formatCount(type.listings)}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      <Link className="qy-link" to={searchBy('category', category.category)} style={{ alignSelf: 'flex-start' }}>
        See all in {category.category}
      </Link>
    </li>
  )
}

export default function Categories() {
  const categories = useApi('/categories?current=true')
  const types = useApi('/product-types?current=true')
  const typesOf = (name) =>
    (types.data ?? []).filter((t) => t.category === name).sort((a, b) => b.listings - a.listings)
  const error = categories.error || types.error

  return (
    <>
      <AppNav />
      <main className="qy-wrap" style={{ paddingBlock: '28px 64px' }}>
        <Breadcrumb current="Categories" />
        <h1 className="qy-h1" style={{ margin: '14px 0 8px' }}>Categories</h1>
        <p className="qy-body" style={{ marginBottom: 28 }}>
          Counts are listings in each store's latest check. Only phones are matched across stores so far.
        </p>
        {error ? (
          <ErrorBlock what="categories" onRetry={() => { categories.retry(); types.retry() }} />
        ) : !categories.data || !types.data ? (
          <div className="qy-split" role="status" aria-label="Loading categories" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
            {[0, 1, 2, 3].map((i) => <div key={i} className="qy-skel" style={{ height: 160, borderRadius: 20 }} />)}
          </div>
        ) : categories.data.length === 0 ? (
          <div className="qy-empty">
            <h2 className="qy-h3">Nothing to browse right now</h2>
            <p className="qy-small">We have no listings from a recent store check. Try again after the next one.</p>
          </div>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(100%, 380px), 1fr))', gap: 16, alignItems: 'start' }}>
            {categories.data.map((category) => (
              <CategoryTile key={category.category} category={category} types={typesOf(category.category)} />
            ))}
          </ul>
        )}
      </main>
      <Footer />
    </>
  )
}
