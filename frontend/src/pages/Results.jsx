import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import AppNav, { Breadcrumb } from '../components/AppNav'
import ErrorBlock from '../components/ErrorBlock'
import Footer from '../components/Footer'
import ProductCard, { CardSkeletons } from '../components/ProductCard'
import { formatCount, formatPrice, isOutdated, timeAgo } from '../lib/format'
import { useApi } from '../lib/useApi'

const PAGE_SIZE = 24
const AVAILABILITY = ['In stock', 'Out of stock', 'Unknown']
const SORTS = {
  products: [['price_asc', 'Lowest listed price'], ['price_desc', 'Highest listed price'], ['retailers', 'Most stores'], ['newest', 'Newest'], ['name', 'Name']],
  listings: [['price_asc', 'Lowest listed price'], ['price_desc', 'Highest listed price'], ['name', 'Name']],
}
const LABELS = { brand: 'Brand', product_type: 'Type', retailer: 'Store', availability: 'Availability', min_price: 'From ₹', max_price: 'Up to ₹' }

function shared(params) {
  const out = new URLSearchParams()
  for (const key of ['q', 'brand', 'product_type', 'min_price', 'max_price']) {
    if (params.get(key)) out.set(key, params.get(key))
  }
  return out
}

function productsPath(params) {
  const out = shared(params)
  if (params.get('min_retailers')) out.set('min_retailers', params.get('min_retailers'))
  return out
}

function listingsPath(params) {
  const out = shared(params)
  out.set('current', 'true') // never offer a price the latest scrape no longer shows
  for (const key of ['retailer', 'availability']) {
    if (params.get(key)) out.set(key, params.get(key))
  }
  return out
}

function withPaging(base, params, kind) {
  const page = Math.max(1, Number(params.get('page')) || 1)
  const out = new URLSearchParams(base)
  const allowed = SORTS[kind].map(([value]) => value)
  const sort = params.get('sort')
  out.set('sort', allowed.includes(sort) ? sort : 'price_asc')
  out.set('limit', String(PAGE_SIZE))
  out.set('offset', String((page - 1) * PAGE_SIZE))
  return out
}

function AvailabilityBadge({ value }) {
  const cls = { 'In stock': 'qy-badge--ok', 'Out of stock': 'qy-badge--err' }[value] ?? ''
  return <span className={`qy-badge ${cls}`}>{value}</span>
}

function ListingRow({ listing }) {
  const type = listing.categories.find((c) => c.product_type)?.product_type
  return (
    <li className="qy-tile qy-listing">
      <div className="qy-stack" style={{ gap: 6, minWidth: 0 }}>
        <h3 className="qy-pcard__name">{listing.name}</h3>
        <p className="qy-small">
          {listing.retailer.name}{type ? ` · ${type}` : ''} · checked {timeAgo(listing.last_seen_at)}
          {isOutdated(listing.last_seen_at) && <strong style={{ color: 'var(--qy-warn)', fontWeight: 500 }}> · may be outdated</strong>}
        </p>
        <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
          <AvailabilityBadge value={listing.availability} />
        </div>
      </div>
      <div className="qy-stack" style={{ gap: 8, alignItems: 'flex-end' }}>
        <span className="qy-price" style={{ fontSize: 18 }}>{formatPrice(listing.price)}</span>
        <a className="qy-btn qy-btn--sm" href={listing.url} target="_blank" rel="noopener noreferrer">
          Go to store<span aria-hidden="true"> ↗</span>
          <span className="qy-honeypot"> (opens {listing.retailer.name} in a new tab)</span>
        </a>
      </div>
    </li>
  )
}

function Select({ label, value, onChange, options }) {
  const id = `filter-${label.toLowerCase().replace(/\W+/g, '-')}`
  return (
    <div className="qy-filter">
      <label className="qy-label" htmlFor={id}>{label}</label>
      <select id={id} className="qy-select" style={{ width: '100%' }} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Any</option>
        {options.map((option) => <option key={option} value={option}>{option}</option>)}
      </select>
    </div>
  )
}

function Filters({ kind, params, update, clear }) {
  const brands = useApi('/brands')
  const types = useApi('/product-types')
  const retailers = useApi('/retailers')
  const [min, setMin] = useState(params.get('min_price') ?? '')
  const [max, setMax] = useState(params.get('max_price') ?? '')

  useEffect(() => {
    setMin(params.get('min_price') ?? '')
    setMax(params.get('max_price') ?? '')
  }, [params])

  const badRange = min !== '' && max !== '' && Number(min) > Number(max)

  function applyPrice(e) {
    e.preventDefault()
    if (!badRange) update({ min_price: min, max_price: max })
  }

  return (
    <aside aria-label="Filters">
      <details className="qy-filters" open={window.innerWidth > 900}>
        <summary>Filters</summary>
        <div className="qy-between" style={{ alignItems: 'center', paddingBottom: 14 }}>
          <h2 className="qy-h3">Filters</h2>
          <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" onClick={clear}>Reset</button>
        </div>
        <Select label="Type" value={params.get('product_type') ?? ''} onChange={(v) => update({ product_type: v })} options={(types.data ?? []).map((t) => t.product_type).sort()} />
        <Select label="Brand" value={params.get('brand') ?? ''} onChange={(v) => update({ brand: v })} options={(brands.data ?? []).map((b) => b.brand).sort((a, b) => a.localeCompare(b))} />
        <form className="qy-filter" onSubmit={applyPrice}>
          <p className="qy-label">Listed price (₹)</p>
          <div className="qy-row" style={{ gap: 8 }}>
            <label className="qy-field" style={{ flex: 1, minWidth: 0 }}>
              <span className="qy-small">Min</span>
              <input className="qy-input qy-num" inputMode="numeric" type="number" min="0" placeholder="0" style={{ minHeight: 40 }} value={min} onChange={(e) => setMin(e.target.value)} />
            </label>
            <label className="qy-field" style={{ flex: 1, minWidth: 0 }}>
              <span className="qy-small">Max</span>
              <input className="qy-input qy-num" inputMode="numeric" type="number" min="0" placeholder="Any" style={{ minHeight: 40 }} value={max} onChange={(e) => setMax(e.target.value)} />
            </label>
          </div>
          {badRange && <p className="qy-form-error" role="alert">Min can't be above max.</p>}
          <button className="qy-btn qy-btn--quiet qy-btn--sm" type="submit" disabled={badRange}>Apply price</button>
        </form>
        {kind === 'products' ? (
          <div className="qy-filter">
            <label className="qy-check">
              <input type="checkbox" checked={params.get('min_retailers') === '2'} onChange={(e) => update({ min_retailers: e.target.checked ? '2' : '' })} />
              Sold at 2 or more stores
            </label>
          </div>
        ) : (
          <>
            <Select label="Store" value={params.get('retailer') ?? ''} onChange={(v) => update({ retailer: v })} options={(retailers.data ?? []).map((r) => r.name)} />
            <Select label="Availability" value={params.get('availability') ?? ''} onChange={(v) => update({ availability: v })} options={AVAILABILITY} />
          </>
        )}
      </details>
    </aside>
  )
}

function Pagination({ total, page, setPage }) {
  const pages = Math.ceil(total / PAGE_SIZE)
  if (pages <= 1) return null
  return (
    <nav aria-label="Pagination" className="qy-row" style={{ justifyContent: 'center', gap: 12, paddingTop: 16 }}>
      <button className="qy-btn qy-btn--quiet qy-btn--sm" type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
      <span className="qy-small qy-num" aria-current="page">Page {page} of {pages}</span>
      <button className="qy-btn qy-btn--quiet qy-btn--sm" type="button" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
    </nav>
  )
}

export default function Results() {
  const [params, setParams] = useSearchParams()
  const q = params.get('q') ?? ''
  const page = Math.max(1, Number(params.get('page')) || 1)

  const productCount = useApi(`/products?${productsPath(params)}&limit=1`)
  const listingCount = useApi(`/listings?${listingsPath(params)}&limit=1`)
  const requested = params.get('view')
  // Matched products first; plain listings when nothing matched.
  const kind = requested === 'listings' || requested === 'products'
    ? requested
    : productCount.loading || productCount.data?.total ? 'products' : 'listings'

  const pathFor = kind === 'products'
    ? `/products?${withPaging(productsPath(params), params, kind)}`
    : `/listings?${withPaging(listingsPath(params), params, kind)}`
  const results = useApi(pathFor)

  function update(changes) {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (!('page' in changes)) next.delete('page')
    setParams(next)
  }

  function clear() {
    setParams(q ? { q } : {})
  }

  const active = Object.keys(LABELS)
    .filter((key) => params.get(key) && (kind === 'listings' || !['retailer', 'availability'].includes(key)))
    .map((key) => ({ key, label: `${LABELS[key]}${key.endsWith('_price') ? '' : ':'} ${key.endsWith('_price') ? formatCount(Number(params.get(key))) : params.get(key)}` }))
  if (kind === 'products' && params.get('min_retailers')) active.push({ key: 'min_retailers', label: '2+ stores' })

  const heading = q ? `Results for “${q}”` : params.get('product_type') ?? 'All products'
  const sort = params.get('sort')
  const sortValue = SORTS[kind].some(([value]) => value === sort) ? sort : 'price_asc'
  const items = results.data?.items ?? []

  return (
    <>
      <AppNav />
      <div className="qy-wrap" style={{ paddingBlock: '28px 8px' }}>
        <Breadcrumb current={q ? 'Search' : 'Browse'} />
        <h1 className="qy-h1" style={{ marginTop: 14 }}>{heading}</h1>
      </div>
      <div className="qy-wrap qy-side" style={{ paddingBlock: '24px 64px' }}>
        <Filters key={kind} kind={kind} params={params} update={update} clear={clear} />
        <main className="qy-stack" style={{ gap: 20, minWidth: 0 }}>
          <div className="qy-tabs" role="tablist" aria-label="Result type">
            <button className="qy-tab-btn" type="button" role="tab" aria-selected={kind === 'products'} onClick={() => update({ view: 'products' })}>
              Matched products <span className="qy-num">{productCount.data ? formatCount(productCount.data.total) : ''}</span>
            </button>
            <button className="qy-tab-btn" type="button" role="tab" aria-selected={kind === 'listings'} onClick={() => update({ view: 'listings' })}>
              All listings <span className="qy-num">{listingCount.data ? formatCount(listingCount.data.total) : ''}</span>
            </button>
          </div>

          <div className="qy-between" style={{ alignItems: 'center' }}>
            <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
              {active.map((filter) => (
                <button key={filter.key} className="qy-chip qy-chip--on" type="button" aria-label={`Remove filter ${filter.label}`} onClick={() => update({ [filter.key]: '' })}>
                  {filter.label} <span className="qy-chip__x" aria-hidden="true">✕</span>
                </button>
              ))}
              {active.length > 0
                ? <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" onClick={clear}>Clear all</button>
                : <span className="qy-small">No filters applied</span>}
            </div>
            <label className="qy-row" style={{ gap: 8 }}>
              <span className="qy-label">Sort</span>
              <select className="qy-select" value={sortValue} onChange={(e) => update({ sort: e.target.value })}>
                {SORTS[kind].map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
          </div>

          {kind === 'listings' && (
            <p className="qy-small">
              Individual store listings, not matched across stores. Only phones are compared so far, so two
              listings here may or may not be the same product.
            </p>
          )}

          {results.error ? (
            <ErrorBlock what="these results" onRetry={results.retry} />
          ) : results.loading && !results.data ? (
            <div className="qy-grid-3" role="status" aria-label="Loading results"><CardSkeletons count={6} /></div>
          ) : items.length === 0 ? (
            <div className="qy-empty">
              <h2 className="qy-h3">{q ? `Nothing found for “${q}”` : 'Nothing matches these filters'}</h2>
              <p className="qy-small">
                {kind === 'products' && listingCount.data?.total
                  ? `No matched products, but ${formatCount(listingCount.data.total)} store listings match.`
                  : active.length ? 'Try removing a filter.' : 'Try a model number or a shorter name.'}
              </p>
              {kind === 'products' && listingCount.data?.total > 0 && (
                <button className="qy-btn" type="button" onClick={() => update({ view: 'listings' })}>Show store listings</button>
              )}
              {active.length > 0 && <button className="qy-btn qy-btn--quiet" type="button" onClick={clear}>Clear filters</button>}
            </div>
          ) : kind === 'products' ? (
            <div className="qy-grid-3">{items.map((product) => <ProductCard key={product.id} product={product} />)}</div>
          ) : (
            <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {items.map((listing) => <ListingRow key={listing.id} listing={listing} />)}
            </ul>
          )}

          {results.data && <Pagination total={results.data.total} page={page} setPage={(n) => update({ page: String(n) })} />}
        </main>
      </div>
      <Footer />
    </>
  )
}
