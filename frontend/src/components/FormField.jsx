export default function FormField({ label, error, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-body text-sm font-semibold text-ink">{label}</span>
      {children}
      {error && <span className="mt-1.5 block font-body text-xs font-semibold text-terracotta-dark">{error}</span>}
    </label>
  )
}

export function inputClasses(hasError) {
  return `
    w-full rounded-chunky-sm border-2 bg-ivory px-4 py-3 font-body text-sm text-ink
    placeholder:text-walnut/40 transition-all duration-150
    focus:outline-none focus:-translate-y-0.5 focus:shadow-brutal-sm
    ${hasError ? 'border-terracotta' : 'border-ink'}
  `
}
