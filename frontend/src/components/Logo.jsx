import { Link } from 'react-router-dom'
import { MARK, WORDMARK } from './brand'

// The Side-eye mark on its own. Tile and pupils follow the brand tokens, so it works in light and dark themes.
export function LogoMark({ size = 32, className = '' }) {
  return (
    <svg className={`qy-mark ${className}`} width={size} height={size} viewBox="0 0 256 256" aria-hidden="true" focusable="false">
      <path className="qy-mark__tile" d={MARK.tile} />
      <path className="qy-mark__eyes" d={MARK.eyes} />
      <path className="qy-mark__pupils" d={MARK.pupils} />
    </svg>
  )
}

export function Wordmark({ height = 22, className = '' }) {
  const width = (height * WORDMARK.width) / WORDMARK.height
  return (
    <svg className={`qy-wordmark ${className}`} width={width} height={height} viewBox={`0 0 ${WORDMARK.width} ${WORDMARK.height}`} aria-hidden="true" focusable="false">
      <path d={WORDMARK.d} fill="currentColor" />
    </svg>
  )
}

export default function Logo({ to = '/' }) {
  return (
    <Link className="qy-logo" to={to} aria-label="Quote Yard home">
      <LogoMark size={34} />
      <Wordmark height={26} />
    </Link>
  )
}
