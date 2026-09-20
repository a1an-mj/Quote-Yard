import { CheckCircle2, XCircle } from 'lucide-react'
import { formatINR } from '../data/mockData'

export default function RetailerCard({ retailer, isLowest, style }) {
  return (
    <div
      style={style}
      className={`
        flex items-center justify-between gap-4 rounded-chunky-sm border-2 p-5 animate-fade-up
        transition-all duration-150 ease-out hover:-translate-y-0.5
        ${isLowest
          ? 'border-ink bg-terracotta text-ivory shadow-brutal'
          : 'border-ink bg-ivory text-ink shadow-brutal-sm'}
      `}
    >
      <div className="min-w-0">
        {isLowest && (
          <span className="mb-1.5 inline-block rounded-full bg-ink px-2.5 py-0.5 font-body text-[11px] font-bold text-ivory">
            Best price
          </span>
        )}
        <p className="truncate font-display text-lg font-semibold">{retailer.name}</p>
        <p className={`font-display text-2xl font-bold ${isLowest ? 'text-ivory' : 'text-terracotta'}`}>
          {formatINR(retailer.price)}
        </p>
        <div className={`mt-1 flex items-center gap-1.5 text-xs font-medium ${isLowest ? 'text-ivory/85' : 'text-walnut/70'}`}>
          {retailer.inStock ? (
            <>
              <CheckCircle2 size={14} /> In Stock
            </>
          ) : (
            <>
              <XCircle size={14} /> Out of Stock
            </>
          )}
        </div>
      </div>

      <a
        href="#"
        onClick={(e) => e.preventDefault()}
        className={`
          shrink-0 whitespace-nowrap rounded-full border-2 px-4 py-2.5 font-display text-sm font-semibold
          transition-all duration-150 hover:-translate-y-0.5
          ${isLowest
            ? 'border-ivory bg-ink text-ivory hover:bg-walnut'
            : 'border-ink bg-ink text-ivory hover:bg-walnut'}
        `}
      >
        Visit Store
      </a>
    </div>
  )
}
