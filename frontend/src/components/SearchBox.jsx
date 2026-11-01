import { useEffect, useId, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import { formatPrice } from '../lib/format'

const RECENT_KEY = 'qy-recent-searches'
const MIN_CHARS = 2
const DEBOUNCE_MS = 250

function readRecent() {
  try {
    const saved = JSON.parse(localStorage.getItem(RECENT_KEY))
    return Array.isArray(saved) ? saved : []
  } catch {
    return []
  }
}

function remember(query) {
  try {
    const next = [query, ...readRecent().filter((q) => q !== query)].slice(0, 5)
    localStorage.setItem(RECENT_KEY, JSON.stringify(next))
  } catch {
    // storage unavailable: no recent searches
  }
}

export default function SearchBox({ compact = false }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const listId = useId()
  const inputId = useId()
  const box = useRef(null)
  const [query, setQuery] = useState(params.get('q') ?? '')
  const [open, setOpen] = useState(false)
  const [results, setResults] = useState([])
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [active, setActive] = useState(-1)
  const trimmed = query.trim()

  useEffect(() => setQuery(params.get('q') ?? ''), [params])

  useEffect(() => {
    if (trimmed.length < MIN_CHARS) {
      setResults([])
      setStatus('idle')
      return undefined
    }
    const controller = new AbortController()
    setStatus('loading')
    const timer = setTimeout(() => {
      api(`/products?q=${encodeURIComponent(trimmed)}&limit=5&sort=retailers`, { signal: controller.signal })
        .then((page) => {
          setResults(page.items)
          setStatus('done')
          setActive(-1)
        })
        .catch((error) => {
          if (error.name !== 'AbortError') setStatus('error')
        })
    }, DEBOUNCE_MS)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [trimmed])

  useEffect(() => {
    const away = (e) => {
      if (!box.current?.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', away)
    return () => document.removeEventListener('mousedown', away)
  }, [])

  const recent = trimmed ? [] : readRecent()
  // Everything the list offers, in order, so the arrow keys can walk it.
  const options = trimmed.length >= MIN_CHARS
    ? [
        ...results.map((p) => ({ id: `p${p.id}`, run: () => goProduct(p) })),
        { id: 'all', run: () => goSearch(trimmed) },
      ]
    : recent.map((q) => ({ id: `r${q}`, run: () => goSearch(q) }))

  function goSearch(q) {
    remember(q)
    setOpen(false)
    navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  function goProduct(product) {
    setOpen(false)
    navigate(`/product/${product.id}`)
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      // Browsers also clear a search field on Escape; keep what was typed.
      e.preventDefault()
      setOpen(false)
      setActive(-1)
    } else if (e.key === 'ArrowDown' && options.length) {
      e.preventDefault()
      setOpen(true)
      setActive((a) => (a + 1) % options.length)
    } else if (e.key === 'ArrowUp' && options.length) {
      e.preventDefault()
      setActive((a) => (a <= 0 ? options.length - 1 : a - 1))
    } else if (e.key === 'Enter' && open && active >= 0 && options[active]) {
      e.preventDefault()
      options[active].run()
    }
  }

  function submit(e) {
    e.preventDefault()
    if (trimmed) goSearch(trimmed)
  }

  const optionId = (index) => `${listId}-${index}`
  const showList = open && (options.length > 0 || status === 'error')

  return (
    <div className={`qy-searchbox ${compact ? '' : 'qy-searchbox--lg'}`} ref={box}>
      <form role="search" className={`qy-search ${compact ? 'qy-search--sm' : ''}`} onSubmit={submit}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true" style={{ color: 'var(--qy-ink)', flex: 'none' }}>
          <circle cx="11" cy="11" r="7" />
          <path d="M20 20l-3.5-3.5" />
        </svg>
        <label htmlFor={inputId} className="qy-honeypot">Search products</label>
        <input
          id={inputId}
          className="qy-searchbox__input"
          type="search"
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList && active >= 0 ? optionId(active) : undefined}
          autoComplete="off"
          maxLength={100}
          placeholder="Search phones, laptops, TVs, appliances…"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
            setActive(-1)
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {!compact && <button className="qy-btn qy-btn--primary" type="submit">Search</button>}
      </form>

      {showList && (
        <ul className="qy-suggest" id={listId} role="listbox" aria-label="Search suggestions">
          {status === 'error' && <li className="qy-small qy-suggest__head" role="presentation">Suggestions aren't available. Press Enter to search.</li>}
          {!trimmed && recent.length > 0 && <li className="qy-label qy-suggest__head" role="presentation">Recent searches</li>}
          {trimmed.length >= MIN_CHARS && results.length > 0 && <li className="qy-label qy-suggest__head" role="presentation">Matched products</li>}
          {options.map((option, index) => {
            const product = trimmed.length >= MIN_CHARS ? results[index] : null
            return (
              <li key={option.id} id={optionId(index)} role="option" aria-selected={active === index}>
                <button type="button" tabIndex={-1} className={`qy-suggest__item ${active === index ? 'qy-suggest__item--on' : ''}`} onMouseDown={(e) => e.preventDefault()} onClick={option.run}>
                  {product ? (
                    <>
                      <span>{product.name}</span>
                      {product.min_price != null && <span className="qy-price qy-small">from {formatPrice(product.min_price)}</span>}
                    </>
                  ) : option.id === 'all' ? (
                    <span className="qy-link">See all results for “{trimmed}”</span>
                  ) : (
                    <span>{option.id.slice(1)}</span>
                  )}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
