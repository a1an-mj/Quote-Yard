import { Link } from 'react-router-dom'
import { Tag } from 'lucide-react'
import Button from '../components/Button'

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-ivory px-4 text-center">
      <span className="flex h-14 w-14 items-center justify-center rounded-full border-2 border-ink bg-terracotta text-ivory">
        <Tag size={26} strokeWidth={2.5} />
      </span>
      <h1 className="font-display text-4xl font-bold text-ink">404</h1>
      <p className="max-w-xs font-body text-walnut">
        This page wandered off. Let's get you back to comparing prices.
      </p>
      <Button as={Link} to="/" size="lg">
        Back to Quote Yard
      </Button>
    </div>
  )
}
