import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles, TrendingDown, Search as SearchIcon } from 'lucide-react'
import Navbar from '../components/Navbar'
import Footer from '../components/Footer'
import Button from '../components/Button'
import GoogleButton from '../components/GoogleButton'
import { categories, products, formatINR, getLowestPrice, getHighestPrice } from '../data/mockData'
import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'

const heroProduct = products.find((p) => p.id === 'nothing-phone-4b')

const steps = [
  {
    n: '01',
    title: 'Search what you need',
    body: 'Type in any phone, laptop, TV or appliance. We already track it across your local stores.',
  },
  {
    n: '02',
    title: 'See every price, side by side',
    body: 'No tabs, no calling shops. Every retailer\u2019s price, stock and store, in one screen.',
  },
  {
    n: '03',
    title: 'Buy from whoever\u2019s cheapest',
    body: 'Head straight to the best deal. Quote Yard never marks anything up.',
  },
]

export default function Landing() {
  const { loginWithGoogle } = useAuth()
  const navigate = useNavigate()

  function handleGoogle() {
    loginWithGoogle()
    navigate('/dashboard')
  }

  const lowest = getLowestPrice(heroProduct)
  const highest = getHighestPrice(heroProduct)
  const savings = highest - lowest

  return (
    <div className="min-h-screen bg-ivory">
      <Navbar variant="marketing" />

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 py-14 sm:px-6 lg:grid-cols-2 lg:items-center lg:gap-8 lg:px-8 lg:py-24">
          <div className="animate-fade-up">
            <span className="inline-flex items-center gap-1.5 rounded-full border-2 border-ink bg-ivory px-3 py-1 font-body text-xs font-bold text-walnut shadow-brutal-sm">
              <Sparkles size={13} className="text-terracotta" />
              Built for Indian shoppers
            </span>

            <h1 className="mt-5 font-display text-[2.6rem] font-bold leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-6xl">
              Same phone.
              <br />
              Never the same
              <br />
              <span className="text-terracotta">price.</span>
            </h1>

            <p className="mt-5 max-w-md font-body text-lg text-walnut">
              Quote Yard checks the price at every store near you &mdash; myG, Oxygen,
              Pittappillil and more &mdash; so you find the better deal before you buy,
              not after.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button as={Link} to="/signup" size="lg" className="sm:w-auto">
                Get Started
                <ArrowRight size={18} />
              </Button>
              <Button as={Link} to="/login" variant="ghost" size="lg" className="sm:w-auto">
                Login
              </Button>
            </div>

            <div className="mt-6 max-w-xs">
              <GoogleButton onClick={handleGoogle} />
            </div>
          </div>

          {/* Floating price comparison showcase */}
          <div className="relative mx-auto w-full max-w-sm lg:mx-0 lg:max-w-none">
            <div className="animate-pop-in rounded-chunky border-2 border-ink bg-walnut p-6 shadow-brutal-lg sm:p-8">
              <p className="font-body text-xs font-semibold uppercase tracking-wide text-ivory/50">
                Comparing right now
              </p>
              <p className="mt-1 font-display text-2xl font-bold text-ivory">{heroProduct.name}</p>
              <p className="font-body text-sm text-ivory/60">{heroProduct.spec}</p>

              <div className="mt-5 space-y-3">
                {heroProduct.retailers.slice(0, 3).map((r, i) => {
                  const isLowest = r.price === lowest
                  return (
                    <div
                      key={r.name}
                      style={{ animationDelay: `${i * 120}ms` }}
                      className={`
                        flex items-center justify-between rounded-chunky-sm border-2 border-ink px-4 py-3 animate-fade-up
                        ${isLowest ? 'bg-terracotta text-ivory' : 'bg-ivory text-ink'}
                      `}
                    >
                      <span className="font-display font-semibold">{r.name}</span>
                      <span className="font-display font-bold">{formatINR(r.price)}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="absolute -bottom-5 -left-4 animate-float rounded-chunky-sm border-2 border-ink bg-olive px-4 py-3 shadow-brutal sm:-left-8">
              <p className="flex items-center gap-1.5 font-display text-sm font-bold text-ivory">
                <TrendingDown size={16} />
                You save {formatINR(savings)}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CATEGORY STRIP */}
      <section className="mx-auto max-w-6xl px-4 pb-4 pt-10 sm:px-6 lg:px-8 lg:pt-14">
        <div className="rounded-chunky border-2 border-ink bg-taupe/10 p-4 shadow-brutal-sm sm:p-5">
          <div className="no-scrollbar flex gap-3 overflow-x-auto">
            {categories.map((c) => (
              <div
                key={c.id}
                className="flex shrink-0 items-center gap-2 rounded-full border-2 border-ink bg-ivory px-4 py-2 font-body text-sm font-semibold text-walnut"
              >
                <span>{c.emoji}</span>
                {c.name}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <h2 className="max-w-lg font-display text-3xl font-bold leading-tight text-ink sm:text-4xl">
          Three steps between you and a better price.
        </h2>

        <div className="mt-10 grid gap-6 sm:grid-cols-3">
          {steps.map((s) => (
            <div
              key={s.n}
              className="rounded-chunky border-2 border-ink bg-ivory p-6 shadow-brutal-sm transition-transform duration-150 hover:-translate-y-1 hover:shadow-brutal"
            >
              <span className="font-display text-4xl font-bold text-terracotta/40">{s.n}</span>
              <h3 className="mt-3 font-display text-lg font-semibold text-ink">{s.title}</h3>
              <p className="mt-2 font-body text-sm leading-relaxed text-walnut">{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* PRODUCT SHOWCASE */}
      <section className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
        <div className="rounded-chunky bg-ink px-5 py-10 text-ivory shadow-brutal-lg sm:px-8 sm:py-12 lg:px-10 lg:py-14">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 className="font-display text-3xl font-bold sm:text-4xl">Popular this week</h2>
              <p className="mt-2 font-body text-ivory/60">Real products, real retailers, real savings.</p>
            </div>
            <Link to="/signup" className="hidden font-display text-sm font-semibold text-terracotta hover:underline sm:inline-flex sm:items-center sm:gap-1">
              See all products <ArrowRight size={15} />
            </Link>
          </div>

          <div className="no-scrollbar mt-8 flex gap-5 overflow-x-auto pb-2">
            {products.slice(0, 5).map((p) => {
              const low = getLowestPrice(p)
              return (
                <div
                  key={p.id}
                  className="w-[220px] shrink-0 rounded-chunky border-2 border-ivory/20 bg-walnut/40 p-5 transition-colors hover:bg-walnut/70"
                >
                  <div className="mb-4 flex h-20 items-center justify-center rounded-chunky-sm bg-ivory/10 text-4xl">
                    {p.image}
                  </div>
                  <p className="font-display text-sm font-semibold leading-snug">{p.name}</p>
                  <p className="mt-1 font-body text-xs text-ivory/50">{p.spec}</p>
                  <p className="mt-3 font-display text-lg font-bold text-terracotta-light">
                    From {formatINR(low)}
                  </p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
        <div className="flex flex-col items-start gap-6 rounded-chunky border-2 border-ink bg-terracotta p-8 text-ivory shadow-brutal-lg sm:p-12 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="font-display text-3xl font-bold leading-tight sm:text-4xl">
              Your next purchase deserves the better price.
            </h2>
            <p className="mt-3 max-w-md font-body text-ivory/90">
              Create your free account and start comparing in under a minute.
            </p>
          </div>
          <Button as={Link} to="/signup" variant="dark" size="lg" className="w-full lg:w-auto">
            <SearchIcon size={18} />
            Start comparing
          </Button>
        </div>
      </section>

      <Footer />
    </div>
  )
}
