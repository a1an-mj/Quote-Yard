export default function CategoryCard({ category, onClick, style }) {
  return (
    <button
      onClick={onClick}
      style={style}
      className="
        group flex shrink-0 flex-col items-start gap-3 rounded-chunky-sm border-2 border-ink
        bg-ivory p-4 text-left shadow-brutal-sm transition-all duration-150 ease-out
        hover:-translate-y-1 hover:shadow-brutal active:translate-y-0 active:shadow-brutal-sm
        w-[132px] sm:w-[150px]
      "
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-terracotta-50 text-2xl transition-transform duration-150 group-hover:scale-110">
        {category.emoji}
      </span>
      <div>
        <p className="font-display text-sm font-semibold leading-tight text-ink">{category.name}</p>
        <p className="font-body text-xs text-walnut/60">{category.count} items</p>
      </div>
    </button>
  )
}
