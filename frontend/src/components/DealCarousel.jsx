import { useRef } from 'react'
import { Link } from 'react-router-dom'
import { formatPrice, timeAgo } from '../lib/format'

function comparison(deal) {
  return deal.kind === 'store_gap'
    ? `${formatPrice(deal.saving)} less than ${deal.compared_retailer}`
    : `${formatPrice(deal.saving)} below its previous price`
}

function DealCard({ deal }) {
  return (
    <li className="qy-tile qy-deal">
      <div className="qy-img" aria-hidden="true" />
      <div className="qy-stack" style={{ gap: 8, minWidth: 0 }}>
        <span className="qy-label">{deal.label}</span>
        <h3 className="qy-pcard__name qy-deal__name" title={deal.name}>{deal.name}</h3>
        <div className="qy-row" style={{ gap: 10, flexWrap: 'wrap' }}>
          <span className="qy-price" style={{ fontSize: 20 }}>{formatPrice(deal.price)}</span>
          <span className="qy-price qy-small" style={deal.kind === 'price_drop' ? { textDecoration: 'line-through' } : undefined}>
            {formatPrice(deal.compared_price)}
          </span>
        </div>
        <span className="qy-badge qy-badge--solid" style={{ alignSelf: 'flex-start' }}>Save {formatPrice(deal.saving)}</span>
        <p className="qy-small">{comparison(deal)}</p>
        <p className="qy-small">{deal.retailer} · checked {timeAgo(deal.checked_at)}</p>
      </div>
    </li>
  )
}

export default function DealCarousel({ deals, loading, error, onRetry }) {
  const track = useRef(null)
  const scroll = (direction) =>
    track.current?.scrollBy({ left: direction * 416, behavior: 'smooth' })

  if (loading) {
    return (
      <div className="qy-deals" role="status" aria-label="Loading today's deals">
        {[0, 1, 2].map((i) => (
          <div key={i} className="qy-tile qy-deal">
            <div className="qy-skel" style={{ aspectRatio: '1 / 1' }} />
            <div className="qy-stack">
              <div className="qy-skel" style={{ height: 12, width: '60%' }} />
              <div className="qy-skel" style={{ height: 36 }} />
              <div className="qy-skel" style={{ height: 22, width: '50%' }} />
            </div>
          </div>
        ))}
      </div>
    )
  }
  if (error) {
    return (
      <div className="qy-empty" role="alert">
        <h3 className="qy-h3">We couldn't load today's deals</h3>
        <p className="qy-small">Our server didn't respond. No prices are shown rather than old ones.</p>
        <button className="qy-btn" type="button" onClick={onRetry}>Try again</button>
      </div>
    )
  }
  if (!deals?.length) {
    return (
      <div className="qy-empty">
        <h3 className="qy-h3">No deals today</h3>
        <p className="qy-small">No tracked price has dropped enough to count. We don't fill this space with anything else.</p>
      </div>
    )
  }
  return (
    <div className="qy-stack" style={{ gap: 16 }}>
      <ul className="qy-deals" ref={track} tabIndex={0} aria-label="Today's deals" style={{ listStyle: 'none', margin: 0, paddingInline: 0 }}>
        {deals.map((deal) => (
          <DealCard key={`${deal.kind}-${deal.name}-${deal.retailer}`} deal={deal} />
        ))}
      </ul>
      <div className="qy-between" style={{ alignItems: 'center' }}>
        <div className="qy-row" style={{ gap: 8 }}>
          <button className="qy-btn qy-btn--icon qy-btn--quiet" type="button" aria-label="Previous deals" onClick={() => scroll(-1)}>←</button>
          <button className="qy-btn qy-btn--icon qy-btn--quiet" type="button" aria-label="Next deals" onClick={() => scroll(1)}>→</button>
        </div>
        <Link className="qy-btn" to="/signup">Sign up to see every store's price</Link>
      </div>
    </div>
  )
}
