import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, TrendingDown } from 'lucide-react'
import Navbar from '../components/Navbar'
import BottomNav from '../components/BottomNav'
import RetailerCard from '../components/RetailerCard'
import { getProductById, getLowestPrice, getHighestPrice, formatINR } from '../data/mockData'

export default function Comparison() {
  const { productId } = useParams()
  const navigate = useNavigate()
  const product = getProductById(productId)

  if (!product) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-ivory px-4 text-center">
        <p className="font-display text-2xl font-bold text-ink">We couldn't find that product</p>
        <Link to="/search" className="font-body text-sm font-semibold text-terracotta hover:underline">
          Back to search
        </Link>
      </div>
    )
  }

  const lowest = getLowestPrice(product)
  const highest = getHighestPrice(product)
  const savings = highest - lowest
  const sortedRetailers = [...product.retailers].sort((a, b) => a.price - b.price)

  return (
    <div className="min-h-screen bg-ivory pb-24 md:pb-12">
      <Navbar variant="app" />

      <div className="mx-auto max-w-3xl px-4 pt-6 sm:px-6 lg:px-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-1.5 font-body text-sm font-semibold text-walnut hover:text-ink"
        >
          <ArrowLeft size={16} />
          Back
        </button>

        <div className="mt-5 flex items-center gap-5 rounded-chunky border-2 border-ink bg-ivory p-5 shadow-brutal-sm sm:p-6">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-chunky-sm bg-taupe/15 text-4xl sm:h-24 sm:w-24 sm:text-5xl">
            {product.image}
          </div>
          <div>
            <h1 className="font-display text-xl font-bold leading-tight text-ink sm:text-2xl">{product.name}</h1>
            <p className="mt-1 font-body text-sm text-walnut/70 sm:text-base">{product.spec}</p>
          </div>
        </div>

        {savings > 0 && (
          <div className="mt-4 flex items-center gap-3 rounded-chunky-sm border-2 border-ink bg-olive px-5 py-4 text-ivory shadow-brutal-olive">
            <TrendingDown size={22} className="shrink-0" />
            <div>
              <p className="font-display text-lg font-bold">You could save {formatINR(savings)}</p>
              <p className="font-body text-xs text-ivory/70">
                Price difference between highest ({formatINR(highest)}) and lowest ({formatINR(lowest)})
              </p>
            </div>
          </div>
        )}

        <h2 className="mt-8 font-display text-lg font-bold text-ink">
          {product.retailers.length} retailers compared
        </h2>

        <div className="mt-4 space-y-3">
          {sortedRetailers.map((r, i) => (
            <RetailerCard
              key={r.name}
              retailer={r}
              isLowest={r.price === lowest}
              style={{ animationDelay: `${i * 80}ms` }}
            />
          ))}
        </div>

        <p className="mt-6 text-center font-body text-xs text-walnut/50">
          Prices shown are for demo purposes and may not reflect real-time availability.
        </p>
      </div>

      <BottomNav />
    </div>
  )
}
