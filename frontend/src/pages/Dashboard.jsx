import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import Navbar from '../components/Navbar'
import BottomNav from '../components/BottomNav'
import SearchBar from '../components/SearchBar'
import CategoryCard from '../components/CategoryCard'
import { ProductCard, DealCard } from '../components/ProductCard'
import { useAuth } from '../context/AuthContext'
import { categories, products, popularComparisons, todaysDeals, getProductById } from '../data/mockData'

function getGreeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const firstName = user?.name?.split(' ')[0] || 'there'

  function handleSearch(query) {
    if (query?.trim()) navigate(`/search?q=${encodeURIComponent(query.trim())}`)
  }

  return (
    <div className="min-h-screen bg-ivory pb-24 md:pb-12">
      <Navbar variant="app" />

      <div className="mx-auto max-w-6xl px-4 pt-8 sm:px-6 lg:px-8">
        <p className="font-body text-sm font-medium text-walnut/70">{getGreeting()},</p>
        <h1 className="mt-0.5 font-display text-3xl font-bold text-ink sm:text-4xl">{firstName} 👋</h1>

        <div className="mt-6 max-w-xl">
          <SearchBar
            placeholder="What are you looking for?"
            onChange={() => {}}
            onSubmit={handleSearch}
            size="lg"
          />
        </div>

        {/* Categories */}
        <section className="mt-10">
          <h2 className="font-display text-xl font-bold text-ink">Categories</h2>
          <div className="no-scrollbar mt-4 flex gap-3 overflow-x-auto pb-1">
            {categories.map((c) => (
              <CategoryCard
                key={c.id}
                category={c}
                onClick={() => navigate(`/search?category=${c.id}`)}
              />
            ))}
          </div>
        </section>

        {/* Popular comparisons */}
        <section className="mt-10">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl font-bold text-ink">Popular comparisons</h2>
            <button
              onClick={() => navigate('/search')}
              className="flex items-center gap-1 font-body text-sm font-semibold text-terracotta hover:underline"
            >
              See all <ArrowRight size={14} />
            </button>
          </div>
          <div className="no-scrollbar mt-4 flex gap-4 overflow-x-auto pb-2">
            {popularComparisons.map((id) => {
              const product = getProductById(id)
              if (!product) return null
              return <ProductCard key={id} product={product} />
            })}
          </div>
        </section>

        {/* Today's deals */}
        <section id="deals" className="mt-10 scroll-mt-20">
          <h2 className="font-display text-xl font-bold text-ink">Today's deals</h2>
          <div className="no-scrollbar mt-4 flex gap-4 overflow-x-auto pb-2">
            {todaysDeals.map(({ productId, tag }) => {
              const product = getProductById(productId)
              if (!product) return null
              return <DealCard key={productId} product={product} tag={tag} />
            })}
          </div>
        </section>

        {/* More to explore */}
        <section className="mt-10">
          <h2 className="font-display text-xl font-bold text-ink">More to explore</h2>
          <div className="no-scrollbar mt-4 flex gap-4 overflow-x-auto pb-2">
            {products.slice(6, 12).map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      </div>

      <BottomNav />
    </div>
  )
}
