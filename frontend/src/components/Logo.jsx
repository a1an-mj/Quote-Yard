import { Link } from 'react-router-dom'

const DOTS = ['', 'o', '', 'o', '', 'o', '', 'o', '']

export default function Logo() {
  return (
    <Link className="qy-logo" to="/" aria-label="Quote Yard home">
      <span className="qy-logo__mark" aria-hidden="true">
        {DOTS.map((cls, i) => (
          <i key={i} className={cls} />
        ))}
      </span>
      Quote Yard
    </Link>
  )
}
