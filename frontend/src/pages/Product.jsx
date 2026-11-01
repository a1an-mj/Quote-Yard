import { Link, useParams } from 'react-router-dom'
import AppNav, { Breadcrumb } from '../components/AppNav'
import ErrorBlock from '../components/ErrorBlock'
import Footer from '../components/Footer'
import PriceChart from '../components/PriceChart'
import ProductActions from '../components/ProductActions'
import { formatPrice, isOutdated, specLine, timeAgo } from '../lib/format'
import { lowestOverTime } from '../lib/history'
import { useApi } from '../lib/useApi'

const OUT = 'Out of stock'

function Availability({ value }) {
  const cls = { 'In stock': 'qy-badge--ok', [OUT]: 'qy-badge--err' }[value] ?? ''
  return <span className={`qy-badge ${cls}`}>{value}</span>
}

function StoreLink({ offer }) {
  return (
    <a className="qy-btn qy-btn--sm" href={offer.url} target="_blank" rel="noopener noreferrer">
      Go to store<span aria-hidden="true"> ↗</span>
      <span className="qy-honeypot"> (opens {offer.retailer.name} in a new tab)</span>
    </a>
  )
}

function Checked({ iso }) {
  return (
    <span className="qy-small">
      {timeAgo(iso)}
      {isOutdated(iso) && <span style={{ display: 'block', color: 'var(--qy-warn)' }}>may be outdated</span>}
    </span>
  )
}

function Summary({ compare }) {
  const rows = compare.retailers
  const buyable = rows.filter((r) => r.best.availability !== OUT)
  if (!buyable.length) {
    return (
      <div className="qy-tile qy-tile--pad qy-stack">
        <h2 className="qy-h3">{rows.length ? `Out of stock at ${rows.length === 1 ? 'the 1 store' : `all ${rows.length} stores`} listing it` : 'No store lists this right now'}</h2>
        <p className="qy-small">We don't show a lowest price when nothing can be bought.</p>
      </div>
    )
  }
  const low = buyable[0]
  if (buyable.length === 1) {
    return (
      <div className="qy-tile qy-tile--pad qy-stack" style={{ gap: 8 }}>
        <p className="qy-label">Only {low.retailer.name} lists this in stock</p>
        <span className="qy-price qy-price--lg">{formatPrice(low.best.price)}</span>
        <p className="qy-small">There's nothing to compare yet, so we show no lowest or highest price.</p>
      </div>
    )
  }
  const high = buyable[buyable.length - 1]
  const lows = buyable.filter((r) => r.cheapest_listed).map((r) => r.retailer.name).join(', ')
  if (low.best.price === high.best.price) {
    return (
      <div className="qy-tile qy-tile--pad qy-stack" style={{ gap: 8 }}>
        <p className="qy-label">Same price at {buyable.length} stores</p>
        <span className="qy-price qy-price--lg">{formatPrice(low.best.price)}</span>
        <p className="qy-small">{lows}</p>
      </div>
    )
  }
  return (
    <div className="qy-tile qy-tile--pad qy-summary">
      <div className="qy-stack" style={{ gap: 4 }}>
        <p className="qy-label">Lowest listed</p>
        <span className="qy-price qy-price--lg">{formatPrice(low.best.price)}</span>
        <p className="qy-small">{lows}</p>
      </div>
      <div className="qy-stack" style={{ gap: 4 }}>
        <p className="qy-label">Highest listed</p>
        <span className="qy-price qy-price--lg">{formatPrice(high.best.price)}</span>
        <p className="qy-small">{high.retailer.name}</p>
      </div>
      <div className="qy-stack" style={{ gap: 4 }}>
        <p className="qy-label">Difference</p>
        <span className="qy-price qy-price--lg">{formatPrice(compare.spread)}</span>
        <p className="qy-small">Between the {buyable.length} stores with stock</p>
      </div>
    </div>
  )
}

function PriceTable({ compare }) {
  const lowest = compare.retailers.find((r) => r.cheapest_listed)?.best.price
  return (
    <div className="qy-tablebox">
      <table className="qy-table">
        <caption className="qy-honeypot">Current prices by store, lowest first</caption>
        <thead>
          <tr>
            <th scope="col">Store</th>
            <th scope="col" className="r">Listed price</th>
            <th scope="col" className="r">vs lowest</th>
            <th scope="col">Availability</th>
            <th scope="col">Checked</th>
            <th scope="col"><span className="qy-honeypot">Store link</span></th>
          </tr>
        </thead>
        <tbody>
          {compare.retailers.map((row) => {
            const out = row.best.availability === OUT
            return (
              <tr key={row.retailer.id} className={row.cheapest_listed ? 'qy-row--best' : out ? 'qy-row--off' : ''}>
                <th scope="row" style={{ font: 'inherit', textAlign: 'left', padding: '16px 20px', textTransform: 'none', letterSpacing: 0, color: 'inherit' }}>
                  <span className="qy-row" style={{ gap: 8, flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 500 }}>{row.retailer.name}</span>
                    {row.cheapest_listed && <span className="qy-badge qy-badge--solid">Lowest</span>}
                  </span>
                  {row.best.box_note && <span className="qy-small" style={{ display: 'block' }}>Sold {row.best.box_note}</span>}
                </th>
                <td className="r"><span className="qy-price">{formatPrice(row.best.price)}</span></td>
                <td className="r"><span className="qy-price qy-small">{out || lowest == null || row.best.price === lowest ? '–' : `+ ${formatPrice(row.best.price - lowest)}`}</span></td>
                <td><Availability value={row.best.availability} /></td>
                <td><Checked iso={row.best.last_seen_at} /></td>
                <td className="r"><StoreLink offer={row.best} /></td>
              </tr>
            )
          })}
          {compare.not_listed.map((name) => (
            <tr key={name} className="qy-row--off">
              <th scope="row" style={{ font: 'inherit', textAlign: 'left', padding: '16px 20px', textTransform: 'none', letterSpacing: 0, color: 'inherit' }}>{name}</th>
              <td colSpan={5}><span className="qy-small">Not found in our latest data. It may still be sold there.</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function OfferList({ offers }) {
  return (
    <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 8 }}>
      {offers.map((offer) => (
        <li key={offer.listing_id} className="qy-tile qy-listing">
          <div className="qy-stack" style={{ gap: 4, minWidth: 0 }}>
            <span style={{ fontSize: 14, fontWeight: 500 }}>{offer.name}</span>
            <span className="qy-small">
              {offer.retailer.name} · {offer.availability} · checked {timeAgo(offer.last_seen_at)}
              {offer.box_note ? ` · ${offer.box_note}` : ''}
            </span>
          </div>
          <div className="qy-row" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <span className="qy-price">{formatPrice(offer.price)}</span>
            <StoreLink offer={offer} />
          </div>
        </li>
      ))}
    </ul>
  )
}

function History({ id }) {
  const state = useApi(`/products/${id}/prices`)
  if (state.error) return <ErrorBlock what="price history" onRetry={state.retry} />
  if (state.loading) return <div className="qy-skel" style={{ height: 200 }} role="status" aria-label="Loading price history" />
  const series = lowestOverTime(state.data.listings)
  if (series.length < 2) {
    return (
      <div className="qy-empty">
        <h3 className="qy-h3">The lowest price hasn't changed yet</h3>
        <p className="qy-small">A chart appears here once we've recorded a change. We check prices every day.</p>
      </div>
    )
  }
  return (
    <div className="qy-tile qy-tile--pad qy-stack" style={{ gap: 16 }}>
      <PriceChart series={series} />
      <details>
        <summary className="qy-small" style={{ cursor: 'pointer', minHeight: 32 }}>Show as a table</summary>
        <div className="qy-tablebox" style={{ marginTop: 8 }}>
          <table className="qy-table">
            <thead><tr><th scope="col">Date</th><th scope="col" className="r">Lowest listed</th></tr></thead>
            <tbody>
              {series.map((point) => (
                <tr key={point.at}>
                  <td>{new Date(point.at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</td>
                  <td className="r"><span className="qy-price">{formatPrice(point.price)}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  )
}

export default function Product() {
  const { id } = useParams()
  const product = useApi(`/products/${id}`)
  const compare = useApi(`/compare/${id}`)
  const variants = useApi(`/products/${id}/variants`)

  const missing = product.error?.status === 404 || product.error?.status === 422
  const data = product.data
  const offers = data?.offers ?? []
  const current = offers.filter((o) => o.current)
  const older = offers.filter((o) => !o.current)

  return (
    <>
      <AppNav />
      <main className="qy-wrap" style={{ paddingBlock: '28px 64px' }}>
        {missing ? (
          <div className="qy-empty">
            <h1 className="qy-h1">Product not found</h1>
            <p className="qy-small">It may have been removed or the link is wrong.</p>
            <Link className="qy-btn" to="/home">Back to home</Link>
          </div>
        ) : product.error ? (
          <ErrorBlock what="this product" onRetry={product.retry} />
        ) : !data ? (
          <div className="qy-stack" role="status" aria-label="Loading product">
            <div className="qy-skel" style={{ height: 40, width: '60%' }} />
            <div className="qy-skel" style={{ height: 120 }} />
            <div className="qy-skel" style={{ height: 240 }} />
          </div>
        ) : (
          <div className="qy-stack" style={{ gap: 32 }}>
            <div className="qy-stack" style={{ gap: 14 }}>
              <Breadcrumb current={data.brand} />
              <p className="qy-label">{data.brand}{data.product_type ? ` · ${data.product_type}` : ''}</p>
              <h1 className="qy-h1">{data.name.split(' [')[0]}</h1>
              <p className="qy-pcard__spec" style={{ fontSize: 14 }}>{specLine(data.specs)}{data.specs.package ? ` · ${data.specs.package}` : ''}</p>
              {variants.data?.length > 1 && (
                <div className="qy-stack" style={{ gap: 8 }}>
                  <p className="qy-label">Variant · prices change with it</p>
                  <div className="qy-row" style={{ flexWrap: 'wrap', gap: 8 }}>
                    {variants.data.map((variant) => (
                      <Link key={variant.id} className="qy-chip qy-variant-chip" to={`/product/${variant.id}`} aria-current={String(variant.id) === id ? 'page' : undefined}>
                        {specLine({ ...variant.specs, network: null })}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <ProductActions productId={data.id} lowest={data.min_price} />

            {compare.error ? (
              <ErrorBlock what="current prices" onRetry={compare.retry} />
            ) : compare.data ? (
              <>
                <Summary compare={compare.data} />
                <section className="qy-stack" style={{ gap: 12 }} aria-labelledby="prices-title">
                  <h2 className="qy-h2" id="prices-title">Where it's listed</h2>
                  <PriceTable compare={compare.data} />
                  <p className="qy-small">
                    Each store's best price for this exact variant, lowest first. Out-of-stock listings never count
                    as lowest. Delivery and offers vary; confirm on the store's page.
                  </p>
                </section>
              </>
            ) : (
              <div className="qy-skel" style={{ height: 240 }} role="status" aria-label="Loading prices" />
            )}

            <section className="qy-stack" style={{ gap: 12 }} aria-labelledby="history-title">
              <div className="qy-stack" style={{ gap: 4 }}>
                <h2 className="qy-h2" id="history-title">Price history</h2>
                <p className="qy-small">The lowest listed price across all stores, as we recorded it.</p>
              </div>
              <History id={id} />
            </section>

            {current.length > compare.data?.retailers.length && (
              <section className="qy-stack" style={{ gap: 12 }} aria-labelledby="all-title">
                <h2 className="qy-h2" id="all-title">All {current.length} listings, including colours</h2>
                <OfferList offers={current} />
              </section>
            )}

            {older.length > 0 && (
              <details className="qy-stack">
                <summary className="qy-small" style={{ cursor: 'pointer', minHeight: 32 }}>{older.length} older {older.length === 1 ? 'listing' : 'listings'}, not in the latest data and not counted above</summary>
                <div style={{ marginTop: 12 }}><OfferList offers={older} /></div>
              </details>
            )}
          </div>
        )}
      </main>
      <Footer />
    </>
  )
}
