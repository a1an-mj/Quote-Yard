import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import { formatPrice } from '../lib/format'
import { hueOf, iconOf, storeHue } from '../lib/look'

// The product type's icon on its category's colour.
export function TypeIcon({ type, category, size = 'md' }) {
  const Icon = iconOf(type, category)
  return (
    <span className={`qy-ticon qy-ticon--${size} qy-hue--${hueOf(category)}`} aria-hidden="true">
      <Icon strokeWidth={1.6} />
    </span>
  )
}

export function StoreName({ name, bold = false }) {
  return (
    <span className="qy-store">
      <span className={`qy-store__dot qy-hue--${storeHue(name)}`} aria-hidden="true" />
      <span style={bold ? { fontWeight: 500 } : undefined}>{name}</span>
    </span>
  )
}

// "↓ ₹2,000" in green or "↑ ₹500" in red, with the words for screen readers.
export function Change({ amount, suffix = '' }) {
  if (!amount) return null
  const down = amount < 0
  const Arrow = down ? ArrowDownRight : ArrowUpRight
  return (
    <span className={`qy-change ${down ? 'qy-change--down' : 'qy-change--up'}`}>
      <Arrow aria-hidden="true" size={14} strokeWidth={2.2} />
      <span className="qy-honeypot">{down ? 'Down' : 'Up'} </span>
      {formatPrice(Math.abs(amount))}{suffix}
    </span>
  )
}
