import { Link } from 'react-router-dom'
import { ArrowRight, Store } from 'lucide-react'
import { getLowestPrice, formatINR } from '../data/mockData'

export function ProductCard({ product, style }) {
  const lowest = getLowestPrice(product)
  const anyInStock = product.retailers.some((r) => r.inStock)

  return (
    <Link
      to={`/compare/${product.id}`}
      style={style}
      className="
        group block shrink-0 rounded-chunky border-2 border-ink bg-ivory p-5
        shadow-brutal-sm transition-all duration-200 ease-out
        hover:-translate-y-1 hover:shadow-brutal
        active:translate-y-0 active:shadow-brutal-sm
        w-[240px] sm:w-[260px]
      "
    >
      <div className="mb-4 flex h-28 items-center justify-center rounded-chunky-sm bg-taupe/15 text-5xl">
        {product.image}
      </div>
      <p className="font-display text-base font-semibold leading-snug text-ink">{product.name}</p>
      <p className="mt-0.5 font-body text-xs text-walnut/60">{product.spec}</p>

      <div className="mt-4 flex items-end justify-between">
        <div>
          <p className="font-body text-[11px] uppercase tracking-wide text-walnut/50">From</p>
          <p className="font-display text-xl font-bold text-terracotta">{formatINR(lowest)}</p>
        </div>
        <div className="flex items-center gap-1 font-body text-xs font-medium text-walnut/70">
          <Store size={14} />
          {product.retailers.length} retailers
        </div>
      </div>

      <div
        className={`mt-2 inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-body text-[11px] font-semibold ${
          anyInStock ? 'bg-olive/15 text-olive-dark' : 'bg-walnut/10 text-walnut/60'
        }`}
      >
        {anyInStock ? 'Available now' : 'Limited availability'}
      </div>

      <div className="mt-4 flex items-center justify-between rounded-full border-2 border-ink bg-ink px-4 py-2.5 font-display text-sm font-semibold text-ivory transition-colors group-hover:bg-walnut">
        Compare prices
        <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
      </div>
    </Link>
  )
}

export function ResultCard({ product, style }) {
  const lowest = getLowestPrice(product)
  const anyInStock = product.retailers.some((r) => r.inStock)

  return (
    <Link
      to={`/compare/${product.id}`}
      style={style}
      className="
        group flex items-center gap-4 rounded-chunky border-2 border-ink bg-ivory p-4
        shadow-brutal-sm transition-all duration-200 ease-out
        hover:-translate-y-1 hover:shadow-brutal active:translate-y-0 active:shadow-brutal-sm
        sm:gap-5 sm:p-5
      "
    >
      <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-chunky-sm bg-taupe/15 text-3xl sm:h-20 sm:w-20 sm:text-4xl">
        {product.image}
      </div>

      <div className="min-w-0 flex-1">
        <p className="truncate font-display text-base font-semibold text-ink sm:text-lg">{product.name}</p>
        <p className="mt-0.5 truncate font-body text-xs text-walnut/60 sm:text-sm">{product.spec}</p>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className="font-display text-lg font-bold text-terracotta sm:text-xl">From {formatINR(lowest)}</span>
          <span className="flex items-center gap-1 font-body text-xs font-medium text-walnut/60">
            <Store size={13} />
            {product.retailers.length} retailers
          </span>
          <span
            className={`rounded-full px-2 py-0.5 font-body text-[11px] font-semibold ${
              anyInStock ? 'bg-olive/15 text-olive-dark' : 'bg-walnut/10 text-walnut/60'
            }`}
          >
            {anyInStock ? 'Available' : 'Limited'}
          </span>
        </div>
      </div>

      <div className="hidden shrink-0 items-center gap-1.5 rounded-full border-2 border-ink bg-ink px-4 py-2.5 font-display text-sm font-semibold text-ivory transition-colors group-hover:bg-walnut sm:flex">
        Compare
        <ArrowRight size={15} className="transition-transform group-hover:translate-x-1" />
      </div>
      <ArrowRight size={20} className="shrink-0 text-ink sm:hidden" />
    </Link>
  )
}

export function DealCard({ product, tag, style }) {
  const lowest = getLowestPrice(product)

  return (
    <Link
      to={`/compare/${product.id}`}
      style={style}
      className="
        group flex shrink-0 items-center gap-4 rounded-chunky-sm border-2 border-ink bg-olive
        p-4 text-ivory shadow-brutal-olive transition-all duration-200 ease-out
        hover:-translate-y-1 active:translate-y-0 active:shadow-brutal-sm
        w-[260px] sm:w-[280px]
      "
    >
      <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-chunky-sm bg-ivory/15 text-3xl">
        {product.image}
      </div>
      <div className="min-w-0">
        <span className="inline-block rounded-full bg-ivory px-2 py-0.5 font-body text-[10px] font-bold text-olive-dark">
          {tag}
        </span>
        <p className="mt-1 truncate font-display text-sm font-semibold">{product.name}</p>
        <p className="font-display text-lg font-bold">{formatINR(lowest)}</p>
      </div>
    </Link>
  )
}
