import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import AppNav, { Breadcrumb } from '../components/AppNav'
import ErrorBlock from '../components/ErrorBlock'
import Field from '../components/Field'
import Footer from '../components/Footer'
import { api, errorMessage } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatPrice, timeAgo } from '../lib/format'
import { useApi } from '../lib/useApi'

const ACTIONS = {
  pending: [['approve', 'Approve', 'qy-btn--primary'], ['reject', 'Reject', 'qy-btn--ghost']],
  approved: [['suspend', 'Suspend', 'qy-btn--ghost']],
  rejected: [['approve', 'Approve', 'qy-btn--quiet']],
  suspended: [['reinstate', 'Reinstate', 'qy-btn--quiet']],
}
const STATUS_BADGE = { approved: 'qy-badge--ok', suspended: 'qy-badge--err', rejected: 'qy-badge--err', pending: '' }

function Block({ state, what, empty, children }) {
  if (state.error) return <ErrorBlock what={what} onRetry={state.retry} />
  if (!state.data) return <div className="qy-skel" style={{ height: 100 }} role="status" aria-label={`Loading ${what}`} />
  if (!state.data.length) return <div className="qy-empty"><p className="qy-small">{empty}</p></div>
  return children
}

export default function Admin() {
  const { user } = useAuth()
  const invites = useApi('/admin/invites')
  const vendors = useApi('/admin/vendors')
  const offers = useApi('/admin/offers')
  const audit = useApi('/admin/audit')
  const [email, setEmail] = useState('')
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  if (!user.is_admin) return <Navigate to="/home" replace />

  async function run(action, ...refresh) {
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await action()
      refresh.forEach((state) => state.retry())
      audit.retry()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const invite = (e) => {
    e.preventDefault()
    run(async () => {
      await api('/admin/invites', { method: 'POST', body: { email } })
      setNotice(`Invite sent to ${email}.`)
      setEmail('')
    }, invites)
  }
  const decide = (vendor, decision) => run(() => api(`/admin/vendors/${vendor.id}/decision`, { method: 'POST', body: { decision } }), vendors, offers)

  return (
    <>
      <AppNav />
      <main className="qy-wrap qy-stack" style={{ paddingBlock: '28px 64px', gap: 40 }}>
        <div className="qy-stack" style={{ gap: 14 }}>
          <Breadcrumb current="Shops" />
          <h1 className="qy-h1">Local shops</h1>
          {error && <p className="qy-form-error" role="alert">{error}</p>}
          {notice && <p className="qy-form-note" role="status">{notice}</p>}
        </div>

        <section className="qy-stack" style={{ gap: 16 }} aria-labelledby="shops-title">
          <h2 className="qy-h2" id="shops-title">Shops</h2>
          <Block state={vendors} what="shops" empty="No shops have joined yet.">
            <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 8 }}>
              {vendors.data?.map((vendor) => (
                <li key={vendor.id} className="qy-tile qy-listing" style={{ flexWrap: 'wrap' }}>
                  <div className="qy-stack" style={{ gap: 4, minWidth: 0 }}>
                    <span className="qy-row" style={{ gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontWeight: 500 }}>{vendor.shop_name}</span>
                      <span className={`qy-badge ${STATUS_BADGE[vendor.status]}`}>{vendor.status}</span>
                    </span>
                    <span className="qy-small">{vendor.owner_name} · {vendor.email} · {vendor.phone}</span>
                    <span className="qy-small">{vendor.address}, {vendor.town}, {vendor.district}</span>
                    <span className="qy-small">GST: {vendor.gst_number ?? 'not given'} · joined {timeAgo(vendor.created_at)}</span>
                  </div>
                  <div className="qy-row" style={{ flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    {ACTIONS[vendor.status].map(([decision, label, style]) => (
                      <button key={decision} className={`qy-btn ${style} qy-btn--sm`} type="button" disabled={busy} aria-label={`${label} ${vendor.shop_name}`} onClick={() => decide(vendor, decision)}>{label}</button>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </Block>
        </section>

        <section className="qy-stack" style={{ gap: 16 }} aria-labelledby="invites-title">
          <h2 className="qy-h2" id="invites-title">Invite a shop</h2>
          <form className="qy-row" style={{ flexWrap: 'wrap', gap: 12, alignItems: 'flex-end' }} onSubmit={invite}>
            <Field id="invite-email" label="Shop's email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            <button className="qy-btn qy-btn--primary" type="submit" disabled={busy}>Send invite</button>
          </form>
          <Block state={invites} what="invites" empty="No invites sent yet.">
            <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 8 }}>
              {invites.data?.map((row) => (
                <li key={row.id} className="qy-tile qy-listing">
                  <span className="qy-small">{row.email} · sent {timeAgo(row.created_at)} · {row.state}</span>
                  {row.state === 'waiting' && <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" disabled={busy} aria-label={`Cancel invite for ${row.email}`} onClick={() => run(() => api(`/admin/invites/${row.id}`, { method: 'DELETE' }), invites)}>Cancel</button>}
                </li>
              ))}
            </ul>
          </Block>
        </section>

        <section className="qy-stack" style={{ gap: 16 }} aria-labelledby="running-title">
          <div className="qy-stack" style={{ gap: 4 }}>
            <h2 className="qy-h2" id="running-title">Running offers</h2>
            <p className="qy-small">Offers from approved shops go live after the automatic checks, without review. Remove any that look wrong.</p>
          </div>
          <Block state={offers} what="offers" empty="No offers are running.">
            <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 8 }}>
              {offers.data?.map((offer) => (
                <li key={offer.id} className="qy-tile qy-listing">
                  <div className="qy-stack" style={{ gap: 4, minWidth: 0 }}>
                    <Link to={`/product/${offer.product_id}`} style={{ fontWeight: 500 }}>{offer.product_name.split(' [')[0]}</Link>
                    <span className="qy-small">{offer.shop_name} · {offer.starts_on} to {offer.ends_on} · {offer.state}</span>
                  </div>
                  <div className="qy-row">
                    <span className="qy-price">{formatPrice(offer.price)}</span>
                    <button className="qy-btn qy-btn--ghost qy-btn--sm" type="button" disabled={busy} aria-label={`Remove ${offer.shop_name} offer on ${offer.product_name}`} onClick={() => run(() => api(`/admin/offers/${offer.id}`, { method: 'DELETE' }), offers)}>Remove</button>
                  </div>
                </li>
              ))}
            </ul>
          </Block>
        </section>

        <details>
          <summary className="qy-small" style={{ cursor: 'pointer', minHeight: 32 }}>Recent activity</summary>
          <div style={{ marginTop: 12 }}>
            <Block state={audit} what="activity" empty="Nothing yet.">
              <ul className="qy-stack" style={{ listStyle: 'none', margin: 0, padding: 0, gap: 4 }}>
                {audit.data?.map((row) => <li key={row.id} className="qy-small">{timeAgo(row.created_at)} · {row.actor} · {row.action}{row.vendor_id ? ` · shop ${row.vendor_id}` : ''}{row.offer_id ? ` · offer ${row.offer_id}` : ''}</li>)}
              </ul>
            </Block>
          </div>
        </details>
      </main>
      <Footer />
    </>
  )
}
