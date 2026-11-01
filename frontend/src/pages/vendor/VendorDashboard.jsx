import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import ErrorBlock from '../../components/ErrorBlock'
import Field from '../../components/Field'
import Footer from '../../components/Footer'
import Logo from '../../components/Logo'
import { api, errorMessage } from '../../lib/api'
import { formatPrice, specLine } from '../../lib/format'
import { useApi } from '../../lib/useApi'

const STATUS = {
  pending: 'Your details are waiting for review. You can publish offers once your shop is approved.',
  rejected: "Your shop wasn't approved, so you can't publish offers.",
  suspended: 'Your shop is suspended and your offers are hidden from customers.',
}
const STATE_BADGE = { live: 'qy-badge--ok', scheduled: '', expired: '', closed: '' }

// Dates in India, whatever the device's clock zone is.
function dateInIndia(addDays = 0) {
  const now = new Date(Date.now() + addDays * 86400000)
  return now.toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' })
}

function NewOffer({ onDone }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [product, setProduct] = useState(null)
  const [price, setPrice] = useState('')
  const [starts, setStarts] = useState(dateInIndia())
  const [ends, setEnds] = useState(dateInIndia(6))
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (product || query.trim().length < 2) {
      setResults([])
      return undefined
    }
    const controller = new AbortController()
    const timer = setTimeout(() => {
      api(`/vendor/products?q=${encodeURIComponent(query.trim())}`, { signal: controller.signal })
        .then(setResults)
        .catch((err) => { if (err.name !== 'AbortError') setError(errorMessage(err)) })
    }, 250)
    return () => { clearTimeout(timer); controller.abort() }
  }, [query, product])

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api('/vendor/offers', { method: 'POST', body: { product_id: product.id, price: Number(price), starts_on: starts, ends_on: ends } })
      setProduct(null)
      setQuery('')
      setPrice('')
      onDone()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="qy-tile qy-tile--pad qy-stack" style={{ gap: 16 }} onSubmit={submit}>
      <h2 className="qy-h3">Add an offer</h2>
      {product ? (
        <div className="qy-row" style={{ justifyContent: 'space-between', flexWrap: 'wrap' }}>
          <div className="qy-stack" style={{ gap: 4 }}>
            <span style={{ fontWeight: 500 }}>{product.name.split(' [')[0]}</span>
            <span className="qy-small">{specLine(product.specs)} · lowest store price {product.min_price != null ? formatPrice(product.min_price) : 'not available'}</span>
          </div>
          <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" onClick={() => setProduct(null)}>Change</button>
        </div>
      ) : (
        <div className="qy-stack" style={{ gap: 8 }}>
          <Field id="find" label="Find the product" autoComplete="off" hint="Search by brand and model. Offers can only be added to products we already list." value={query} onChange={(e) => setQuery(e.target.value)} />
          {results.map((item) => (
            <button key={item.id} className="qy-btn qy-btn--quiet qy-btn--sm" style={{ justifyContent: 'flex-start', textAlign: 'left', height: 'auto', paddingBlock: 8 }} type="button" onClick={() => setProduct(item)}>
              {item.name.split(' [')[0]} · {specLine(item.specs)}
            </button>
          ))}
          {query.trim().length >= 2 && results.length === 0 && <p className="qy-small">No products found yet.</p>}
        </div>
      )}
      {product && (
        <>
          <Field id="price" label="Your price (₹)" type="number" inputMode="numeric" min="1" step="1" required value={price} onChange={(e) => setPrice(e.target.value)} />
          <div className="qy-row" style={{ flexWrap: 'wrap', gap: 16 }}>
            <Field id="starts" label="Starts" type="date" required value={starts} onChange={(e) => setStarts(e.target.value)} />
            <Field id="ends" label="Ends" type="date" required value={ends} onChange={(e) => setEnds(e.target.value)} />
          </div>
          <p className="qy-small">Your offer appears to customers on the start date, with your shop name, town, district, phone number and a map link.</p>
          <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>{busy ? 'Publishing…' : 'Publish offer'}</button>
        </>
      )}
      {error && <p className="qy-form-error" role="alert">{error}</p>}
    </form>
  )
}

function OfferRow({ offer, canEdit, onChange }) {
  const [editing, setEditing] = useState(false)
  const [price, setPrice] = useState(offer.price)
  const [ends, setEnds] = useState(offer.ends_on)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const open = offer.state === 'live' || offer.state === 'scheduled'

  async function run(action) {
    setBusy(true)
    setError(null)
    try {
      await action()
      setEditing(false)
      onChange()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }
  const save = (e) => {
    e.preventDefault()
    run(() => api(`/vendor/offers/${offer.id}`, { method: 'PUT', body: { price: Number(price), starts_on: offer.starts_on, ends_on: ends } }))
  }

  return (
    <li className="qy-tile qy-listing" style={{ flexWrap: 'wrap' }}>
      <div className="qy-stack" style={{ gap: 4, minWidth: 0 }}>
        <span style={{ fontSize: 14, fontWeight: 500 }}>{offer.product.name.split(' [')[0]}</span>
        <span className="qy-small">{offer.starts_on} to {offer.ends_on} · lowest store price {offer.product.min_price != null ? formatPrice(offer.product.min_price) : 'not available'}</span>
        {offer.closed_by === 'admin' && <span className="qy-small">Removed by Quote Yard</span>}
      </div>
      <div className="qy-row" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <span className="qy-price">{formatPrice(offer.price)}</span>
        <span className={`qy-badge ${STATE_BADGE[offer.state]}`}>{offer.state}</span>
        {open && canEdit && <button className="qy-btn qy-btn--quiet qy-btn--sm" type="button" aria-expanded={editing} onClick={() => setEditing(!editing)}>Edit</button>}
        {open && <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" disabled={busy} onClick={() => run(() => api(`/vendor/offers/${offer.id}`, { method: 'DELETE' }))}>Take down</button>}
      </div>
      {editing && (
        <form className="qy-row" style={{ flexWrap: 'wrap', gap: 12, width: '100%', alignItems: 'flex-end' }} onSubmit={save}>
          <Field id={`price-${offer.id}`} label="Price (₹)" type="number" min="1" step="1" required value={price} onChange={(e) => setPrice(e.target.value)} />
          <Field id={`ends-${offer.id}`} label="Ends" type="date" required value={ends} onChange={(e) => setEnds(e.target.value)} />
          <button className="qy-btn qy-btn--primary qy-btn--sm" type="submit" disabled={busy}>Save</button>
        </form>
      )}
      {error && <p className="qy-form-error" role="alert" style={{ width: '100%' }}>{error}</p>}
    </li>
  )
}

export default function VendorDashboard() {
  const navigate = useNavigate()
  const me = useApi('/vendor/me')
  const offers = useApi('/vendor/offers')

  if (me.error?.status === 401) return <Navigate to="/vendor/login" replace />

  async function leave() {
    await api('/vendor/logout', { method: 'POST' })
    navigate('/vendor/login', { replace: true })
  }

  const vendor = me.data
  const approved = vendor?.status === 'approved'
  return (
    <>
      <header className="qy-nav">
        <div className="qy-wrap qy-nav__in" style={{ justifyContent: 'space-between' }}>
          <Logo to="/vendor" />
          <button className="qy-btn qy-btn--ghost" type="button" onClick={leave}>Log out</button>
        </div>
      </header>
      <main className="qy-wrap qy-stack" style={{ paddingBlock: '28px 64px', gap: 32 }}>
        {me.error ? <ErrorBlock what="your shop" onRetry={me.retry} /> : !vendor ? (
          <div className="qy-skel" style={{ height: 120 }} role="status" aria-label="Loading your shop" />
        ) : (
          <>
            <div className="qy-stack" style={{ gap: 8 }}>
              <h1 className="qy-h1">{vendor.shop_name}</h1>
              <p className="qy-small">{vendor.address}, {vendor.town}, {vendor.district} · {vendor.phone}</p>
              {STATUS[vendor.status] && <p className="qy-form-note" role="status">{STATUS[vendor.status]}</p>}
            </div>
            {approved && <NewOffer onDone={offers.retry} />}
            <section className="qy-stack" style={{ gap: 12 }} aria-labelledby="offers-title">
              <h2 className="qy-h2" id="offers-title">Your offers{offers.data ? ` · ${offers.data.length}` : ''}</h2>
              {offers.error ? <ErrorBlock what="your offers" onRetry={offers.retry} /> : !offers.data ? (
                <div className="qy-skel" style={{ height: 80 }} role="status" aria-label="Loading offers" />
              ) : offers.data.length === 0 ? (
                <div className="qy-empty"><h3 className="qy-h3">No offers yet</h3></div>
              ) : (
                <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 8 }}>
                  {offers.data.map((offer) => <OfferRow key={offer.id} offer={offer} canEdit={approved} onChange={offers.retry} />)}
                </ul>
              )}
            </section>
          </>
        )}
      </main>
      <Footer />
    </>
  )
}
