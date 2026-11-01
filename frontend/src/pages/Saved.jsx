import { useState } from 'react'
import { Link } from 'react-router-dom'
import AppNav, { Breadcrumb } from '../components/AppNav'
import ErrorBlock from '../components/ErrorBlock'
import Footer from '../components/Footer'
import ProductCard, { CardSkeletons } from '../components/ProductCard'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatPrice, specLine, timeAgo } from '../lib/format'
import { useApi } from '../lib/useApi'

function priceChange(item) {
  const now = item.product.min_price
  const then = item.price_when_saved
  if (now == null || then == null || now === then) return null
  return now < then
    ? `${formatPrice(then - now)} lower than when you saved it`
    : `${formatPrice(now - then)} higher than when you saved it`
}

function alertStatus(item) {
  const low = item.product.min_price
  if (low == null) return { label: 'No current offer', cls: '' }
  if (low < item.target_price) {
    return item.last_notified_at
      ? { label: 'Price reached', cls: 'qy-badge--ok' }
      : { label: 'Reached, email after next check', cls: 'qy-badge--ok' }
  }
  return { label: 'Watching', cls: '' }
}

export default function Saved() {
  const { user } = useAuth()
  const saved = useApi('/me/saved')
  const alerts = useApi('/me/alerts')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function remove(path, state) {
    setBusy(true)
    setError(null)
    try {
      await api(path, { method: 'DELETE' })
      state.retry()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <AppNav />
      <main className="qy-wrap qy-stack" style={{ paddingBlock: '28px 64px', gap: 40 }}>
        <div className="qy-stack" style={{ gap: 14 }}>
          <Breadcrumb current="Saved & alerts" />
          <h1 className="qy-h1">Your saved items and alerts</h1>
          <p className="qy-small">
            {[user.first_name, user.last_name].filter(Boolean).join(' ')} · {user.email}
          </p>
          {error && <p className="qy-form-error" role="alert">{error}</p>}
        </div>

        <section className="qy-stack" style={{ gap: 16 }} aria-labelledby="saved-title">
          <h2 className="qy-h2" id="saved-title">Saved{saved.data ? ` · ${saved.data.length}` : ''}</h2>
          {saved.error ? (
            <ErrorBlock what="your saved items" onRetry={saved.retry} />
          ) : saved.loading && !saved.data ? (
            <div className="qy-grid-4" role="status" aria-label="Loading saved items"><CardSkeletons /></div>
          ) : saved.data.length === 0 ? (
            <div className="qy-empty">
              <h3 className="qy-h3">Nothing saved yet</h3>
              <p className="qy-small">Open a product and press Save to keep it here.</p>
              <Link className="qy-btn" to="/categories">Browse categories</Link>
            </div>
          ) : (
            <div className="qy-grid-4">
              {saved.data.map((item) => (
                <div key={item.product.id} className="qy-stack" style={{ gap: 8 }}>
                  <ProductCard product={item.product} />
                  {priceChange(item) && <p className="qy-small">{priceChange(item)}</p>}
                  <button className="qy-btn qy-btn--quiet qy-btn--sm" type="button" disabled={busy} aria-label={`Remove ${item.product.name} from saved`} onClick={() => remove(`/me/saved/${item.product.id}`, saved)}>Remove</button>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="qy-stack" style={{ gap: 16 }} aria-labelledby="alerts-title">
          <div className="qy-stack" style={{ gap: 4 }}>
            <h2 className="qy-h2" id="alerts-title">Price alerts{alerts.data ? ` · ${alerts.data.length}` : ''}</h2>
            <p className="qy-small">We check prices once a day and email {user.email} when the lowest price goes below your amount.</p>
          </div>
          {alerts.error ? (
            <ErrorBlock what="your alerts" onRetry={alerts.retry} />
          ) : alerts.loading && !alerts.data ? (
            <div className="qy-skel" style={{ height: 120 }} role="status" aria-label="Loading alerts" />
          ) : alerts.data.length === 0 ? (
            <div className="qy-empty">
              <h3 className="qy-h3">No alerts yet</h3>
              <p className="qy-small">Open a product and press Set price alert.</p>
            </div>
          ) : (
            <div className="qy-tablebox">
              <table className="qy-table">
                <caption className="qy-honeypot">Your price alerts</caption>
                <thead>
                  <tr>
                    <th scope="col">Product</th>
                    <th scope="col" className="r">Alert below</th>
                    <th scope="col" className="r">Lowest now</th>
                    <th scope="col">Status</th>
                    <th scope="col"><span className="qy-honeypot">Actions</span></th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.data.map((item) => {
                    const status = alertStatus(item)
                    return (
                      <tr key={item.product.id}>
                        <td>
                          <Link to={`/product/${item.product.id}`} style={{ fontWeight: 500 }}>{item.product.name.split(' [')[0]}</Link>
                          <span className="qy-pcard__spec" style={{ display: 'block' }}>{specLine(item.product.specs)}</span>
                        </td>
                        <td className="r"><span className="qy-price">{formatPrice(item.target_price)}</span></td>
                        <td className="r">{item.product.min_price != null ? <span className="qy-price">{formatPrice(item.product.min_price)}</span> : <span className="qy-missing">None</span>}</td>
                        <td>
                          <span className={`qy-badge ${status.cls}`}>{status.label}</span>
                          {item.last_notified_at && <span className="qy-small" style={{ display: 'block', marginTop: 4 }}>Emailed {timeAgo(item.last_notified_at)}</span>}
                        </td>
                        <td className="r">
                          <div className="qy-row" style={{ justifyContent: 'flex-end', gap: 8 }}>
                            <Link className="qy-btn qy-btn--quiet qy-btn--sm" to={`/product/${item.product.id}`}>Edit</Link>
                            <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" disabled={busy} aria-label={`Remove alert for ${item.product.name}`} onClick={() => remove(`/me/alerts/${item.product.id}`, alerts)}>Remove</button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
      <Footer />
    </>
  )
}
