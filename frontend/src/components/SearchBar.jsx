import { Search } from 'lucide-react'
import { useState } from 'react'

export default function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = 'Search phones, laptops, TVs...',
  autoFocus = false,
  size = 'md',
}) {
  const [focused, setFocused] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    onSubmit?.(value)
  }

  const padding = size === 'lg' ? 'py-4 pl-14 pr-5 text-base' : 'py-3.5 pl-12 pr-4 text-sm'

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div
        className={`
          relative flex items-center rounded-full border-2 border-ink bg-ivory
          transition-all duration-200 ease-out
          ${focused ? 'shadow-brutal-terracotta -translate-y-0.5' : 'shadow-brutal-sm'}
        `}
      >
        <Search
          size={size === 'lg' ? 22 : 18}
          className={`absolute left-4 transition-colors ${focused ? 'text-terracotta' : 'text-walnut/60'}`}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          autoFocus={autoFocus}
          placeholder={placeholder}
          className={`w-full bg-transparent font-body font-medium text-ink placeholder:text-walnut/50 focus:outline-none ${padding}`}
        />
      </div>
    </form>
  )
}
