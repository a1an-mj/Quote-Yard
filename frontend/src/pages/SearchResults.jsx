import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { SlidersHorizontal, SearchX } from 'lucide-react'
import Navbar from '../components/Navbar'
import BottomNav from '../components/BottomNav'
import SearchBar from '../components/SearchBar'
import { ResultCard } from '../components/ProductCard'
import { categories, products, getLowestPrice } from '../data/mockData'

const sortOptions = [
  { id: 'relevance', label: 'Relevance' },
  { id: 'low-high', label: 'Price: Low to High' },
  { id: 'high-low', label: 'Price: High to Low' },
]

export default function SearchResults() {
  const [params, setParams] = useSearchParams()
  const navigate = useNavigate()

  const initialQuery = params.get('q') || ''
  const initialCategory = params.get('category') || 'all'

  const [query, setQuery] = useState(initialQuery)
  const [activeCategory, setActiveCategory] = useState(initialCategory)
  const [sort, setSort] = useState('relevance')
  const [showFilters, setShowFilters] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    setQuery(params.get('q') || '')
    setActiveCategory(params.get('category') || 'all')
  }, [params])

  useEffect(() => {
    setIsLoading(true)
    const t = setTimeout(() => setIsLoading(false), 350)
    return () => clearTimeout(t)
  }, [query, activeCategory, sort])

  function handleSubmit(q) {
    const next = new URLSearchParams(params)
    if (q) next.set('q', q)
    else next.delete('q')
    setParams(next)
  }

  function handleCategory(id) {
    const next = new URLSearchParams(params)
    if (id === 'all') next.delete('category')
    else next.set('category', id)
    setParams(next)
  }

  const results = useMemo(() => {
    let list = products
    if (activeCategory !== 'all') list = list.filter((p) => p.category === activeCategory)
    if (query.trim()) {
      const q = query.trim().toLowerCase()
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.spec.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q)
      )
    }
    const sorted = [...list]
    if (sort === 'low-high') sorted.sort((a, b) => getLowestPrice(a) - getLowestPrice(b))
    if (sort === 'high-low') sorted.sort((a, b) => getLowestPrice(b) - getLowestPrice(a))
    return sorted
  }, [query, activeCategory, sort])

  return (
    <div className="min-h-screen bg-ivory pb-24 md:pb-12">
      <Navbar variant="app" />

      <div className="mx-auto max-w-4xl px-4 pt-8 sm:px-6 lg:px-8">
        <h1 className="font-display text-2xl font-bold text-ink sm:text-3xl">Find and compare</h1>

        <div className="mt-5">
          <SearchBar value={query} onChange={setQuery} onSubmit={handleSubmit} size="lg" autoFocus />
        </div>

        <div className="mt-4 flex items-center justify-between gap-3">
          <div className="no-scrollbar flex flex-1 gap-2 overflow-x-auto">
            <button
              onClick={() => handleCategory('all')}
              className={`shrink-0 rounded-full border-2 border-ink px-4 py-1.5 font-body text-sm font-semibold transition-colors ${
                activeCategory === 'all' ? 'bg-ink text-ivory' : 'bg-ivory text-walnut hover:bg-ink/5'
              }`}
            >
              All
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                onClick={() => handleCategory(c.id)}
                className={`shrink-0 rounded-full border-2 border-ink px-4 py-1.5 font-body text-sm font-semibold transition-colors ${
                  activeCategory === c.id ? 'bg-ink text-ivory' : 'bg-ivory text-walnut hover:bg-ink/5'
                }`}
              >
                {c.emoji} {c.name}
              </button>
            ))}
          </div>

          <button
            onClick={() => setShowFilters((s) => !s)}
            className="flex shrink-0 items-center gap-1.5 rounded-full border-2 border-ink bg-ivory px-3.5 py-1.5 font-body text-sm font-semibold text-ink shadow-brutal-sm"
          >
            <SlidersHorizontal size={15} />
            Sort
          </button>
        </div>

        {showFilters && (
          <div className="mt-3 flex flex-wrap gap-2 rounded-chunky-sm border-2 border-ink bg-taupe/10 p-3 animate-fade-up">
            {sortOptions.map((opt) => (
              <button
                key={opt.id}
                onClick={() => setSort(opt.id)}
                className={`rounded-full px-3.5 py-1.5 font-body text-xs font-semibold transition-colors ${
                  sort === opt.id ? 'bg-terracotta text-ivory' : 'bg-ivory text-walnut border border-ink/20'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        )}

        <p className="mt-5 font-body text-sm text-walnut/60">
          {isLoading ? 'Searching…' : `${results.length} result${results.length === 1 ? '' : 's'}`}
        </p>

        <div className="mt-3 space-y-4 pb-10">
          {isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="flex items-center gap-4 rounded-chunky border-2 border-ink/10 bg-taupe/10 p-5"
              >
                <div className="h-16 w-16 animate-pulse rounded-chunky-sm bg-taupe/30 sm:h-20 sm:w-20" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 w-2/3 animate-pulse rounded bg-taupe/30" />
                  <div className="h-3 w-1/3 animate-pulse rounded bg-taupe/20" />
                  <div className="h-5 w-1/2 animate-pulse rounded bg-taupe/30" />
                </div>
              </div>
            ))}

          {!isLoading && results.map((p) => <ResultCard key={p.id} product={p} />)}

          {!isLoading && results.length === 0 && (
            <div className="flex flex-col items-center gap-3 rounded-chunky border-2 border-dashed border-ink/30 py-16 text-center">
              <SearchX size={32} className="text-walnut/40" />
              <p className="font-display text-lg font-semibold text-ink">No matches yet</p>
              <p className="max-w-xs font-body text-sm text-walnut/60">
                Try a different name, or browse a category instead.
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="mt-2 font-body text-sm font-semibold text-terracotta hover:underline"
              >
                Back to Home
              </button>
            </div>
          )}
        </div>
      </div>

      <BottomNav />
    </div>
  )
}
