import { Link } from 'react-router-dom'
import { formatPrice, specLine } from '../lib/format'

export default function ProductCard({ product }) {
  const stores = product.retailers
  return (
    <Link className="qy-pcard" to={`/product/${product.id}`}>
      <div className="qy-img" aria-hidden="true">
        <span className="qy-img__tag">{product.product_type ?? 'Product'}</span>
      </div>
      <div className="qy-pcard__body">
        <h3 className="qy-pcard__name">{product.name.split(' [')[0]}</h3>
        <p className="qy-pcard__spec">{specLine(product.specs)}</p>
      </div>
      <div className="qy-pcard__foot">
        <div className="qy-stack" style={{ gap: 2 }}>
          <span className="qy-label">{stores > 1 ? 'Lowest listed' : 'Listed'}</span>
          {product.min_price != null
            ? <span className="qy-price">{formatPrice(product.min_price)}</span>
            : <span className="qy-missing">Out of stock</span>}
        </div>
        <span className="qy-small">{stores} {stores === 1 ? 'store' : 'stores'}</span>
      </div>
    </Link>
  )
}

export function CardSkeletons({ count = 4 }) {
  return Array.from({ length: count }, (_, i) => (
    <div key={i} className="qy-pcard" aria-hidden="true">
      <div className="qy-skel" style={{ aspectRatio: '4 / 1', borderRadius: 12 }} />
      <div className="qy-skel" style={{ height: 16 }} />
      <div className="qy-skel" style={{ height: 12, width: '60%' }} />
      <div className="qy-skel" style={{ height: 22, width: '50%' }} />
    </div>
  ))
}
