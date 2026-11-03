import { Link } from 'react-router-dom'
import { formatPrice, specLine } from '../lib/format'
import { hueOf } from '../lib/look'
import { TypeIcon } from './Look'

export default function ProductCard({ product }) {
  const stores = product.retailers
  return (
    <Link className={`qy-pcard qy-hue--${hueOf(product.category)}`} to={`/product/${product.id}`}>
      <div className="qy-pcard__top">
        <TypeIcon type={product.product_type} category={product.category} />
        <span className="qy-pcard__type">{product.product_type ?? product.category ?? 'Product'}</span>
      </div>
      <div className="qy-pcard__body">
        <h3 className="qy-pcard__name">{product.name.split(' [')[0]}</h3>
        <p className="qy-pcard__spec">{specLine(product.specs)}</p>
      </div>
      <div className="qy-pcard__foot">
        <div className="qy-stack" style={{ gap: 2 }}>
          <span className={`qy-label ${stores > 1 ? 'qy-good' : ''}`}>{stores > 1 ? 'Lowest listed' : 'Listed'}</span>
          {product.min_price != null
            ? <span className={`qy-price ${stores > 1 ? 'qy-good' : ''}`}>{formatPrice(product.min_price)}</span>
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
