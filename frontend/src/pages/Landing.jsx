import { useCallback, useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { Link } from 'react-router-dom'
import {
  AirVent, ArrowRight, Laptop, Menu, Microwave, Refrigerator, Smartphone, Tag, Tv, WashingMachine, X,
} from 'lucide-react'
import Footer from '../components/Footer'
import Logo from '../components/Logo'
import ThemeSwitch from '../components/ThemeSwitch'
import { useAuth } from '../lib/auth'
import { formatCount, formatPrice, timeAgo } from '../lib/format'
import { storeHue } from '../lib/look'
import { useApi } from '../lib/useApi'
import '../styles/landing.css'

const SCENES = [
  ['One product. Four stores. Four prices.', 'The same TV or phone is listed at a different price in every store. Checking each one yourself takes a whole evening.'],
  ['We match the exact variant.', 'An 8 GB / 256 GB phone is never compared with the 128 GB one. Only the same model and configuration sit together.'],
  ['The lowest price, in green.', 'Every store we track, cheapest first, with how much you save. Then you buy on the store’s own page.'],
]

// An illustration for the story, not real prices or real stores.
const EXAMPLE = [
  { store: 'Store A', price: 54499 },
  { store: 'Store B', price: 49990 },
  { store: 'Store C', price: 51200 },
  { store: 'Store D', price: 48730 },
]

const ICONS = [
  [/\b(tv|television|qled|oled|uhd)\b/i, Tv], [/\b(phone|galaxy|iphone|redmi|vivo|oppo|5g)\b/i, Smartphone],
  [/\b(laptop|ideapad|vivobook|macbook)\b/i, Laptop], [/\b(ac|air conditioner|\d(\.\d)? ton)\b/i, AirVent],
  [/\b(refrigerator|fridge)\b/i, Refrigerator], [/\b(washing machine|washer)\b/i, WashingMachine],
  [/\bmicrowave\b/i, Microwave],
]
const iconFor = (name) => ICONS.find(([re]) => re.test(name))?.[1] ?? Tag
const shortName = (name) => name.split(/\s[[|(]/)[0]

function usePrefersLessMotion() {
  const [less, setLess] = useState(() => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false)
  useEffect(() => {
    const query = window.matchMedia?.('(prefers-reduced-motion: reduce)')
    if (!query) return undefined
    const change = () => setLess(query.matches)
    query.addEventListener('change', change)
    return () => query.removeEventListener('change', change)
  }, [])
  return less
}

function useSeen(ref) {
  const [seen, setSeen] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el || seen) return undefined
    const io = new IntersectionObserver(([entry]) => entry.isIntersecting && setSeen(true), { threshold: 0.3 })
    io.observe(el)
    return () => io.disconnect()
  }, [ref, seen])
  return seen
}

// Counts up once, when first seen.
function CountUp({ value }) {
  const ref = useRef(null)
  const seen = useSeen(ref)
  const less = usePrefersLessMotion()
  const [shown, setShown] = useState(0)
  useEffect(() => {
    if (value == null || !seen) return undefined
    if (less) { setShown(value); return undefined }
    let frame
    const start = performance.now()
    const tick = (now) => {
      const t = Math.min(1, (now - start) / 1500)
      setShown(Math.round(value * (1 - (1 - t) ** 3)))
      if (t < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [value, seen, less])
  return <span ref={ref}>{value == null ? '–' : formatCount(shown)}</span>
}

function LandingNav() {
  const { user } = useAuth()
  const [open, setOpenNow] = useState(false)
  const [closing, setClosing] = useState(false)
  const less = usePrefersLessMotion()
  // Closing plays a short fade before the menu goes away.
  const setOpen = (value) => {
    if (value || less) { setClosing(false); setOpenNow(value); return }
    setClosing(true)
    setTimeout(() => { setOpenNow(false); setClosing(false) }, 300)
  }

  useEffect(() => {
    if (!open) return undefined
    document.body.style.overflow = 'hidden'
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('keydown', onKey)
    return () => { document.body.style.overflow = ''; window.removeEventListener('keydown', onKey) }
  }, [open])

  const links = [['#deals', "Today's deals"], ['#stores', 'Stores'], ['#how', 'How it works']]
  return (
    <header className="ql-nav">
      <div className="qy-wrap ql-nav__in">
        <Logo />
        <nav className="ql-nav__links" aria-label="Main">
          {links.map(([href, label]) => <a key={href} className="qy-navlink" href={href}>{label}</a>)}
        </nav>
        <div className="ql-nav__end">
          <ThemeSwitch />
          {user ? (
            <Link className="qy-btn qy-btn--primary" to="/home">Open Quote Yard</Link>
          ) : (
            <>
              <Link className="qy-btn qy-btn--ghost" to="/login">Log in</Link>
              <Link className="qy-btn qy-btn--primary" to="/signup">Sign up</Link>
            </>
          )}
        </div>
        <button className="qy-btn qy-btn--quiet ql-nav__menu" type="button" aria-expanded={open} aria-controls="ql-menu" onClick={() => setOpen(true)}>
          <Menu size={18} aria-hidden="true" /> Menu
        </button>
      </div>
      {open && createPortal(
        <div id="ql-menu" className={`ql-overlay ${closing ? 'is-closing' : ''}`} role="dialog" aria-modal="true" aria-label="Menu">
          <div className="ql-overlay__top">
            <span className="ql-overlay__brand">Quote Yard</span>
            <button className="ql-overlay__close" type="button" aria-label="Close menu" onClick={() => setOpen(false)} autoFocus>
              <X size={20} aria-hidden="true" />
            </button>
          </div>
          <nav className="ql-overlay__links" aria-label="Menu links">
            {links.map(([href, label]) => <a key={href} href={href} onClick={() => setOpen(false)}>{label}</a>)}
            {!user && <Link to="/login">Log in</Link>}
          </nav>
          <div className="ql-overlay__foot">
            <Link className="qy-btn qy-btn--primary" to={user ? '/home' : '/signup'}>
              {user ? 'Open Quote Yard' : 'Sign up free'} <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <ThemeSwitch />
          </div>
        </div>,
        document.body,
      )}
    </header>
  )
}

function DealRows({ deal }) {
  const gap = deal.kind === 'store_gap'
  return (
    <ul className="ql-rows">
      <li className="ql-row ql-row--low">
        <span className={`qy-store__dot qy-hue--${storeHue(deal.retailer)}`} aria-hidden="true" />
        <span className="ql-row__store">{deal.retailer}{gap ? '' : ' · now'}</span>
        <span className="ql-row__price">{formatPrice(deal.price)}</span>
      </li>
      <li className="ql-row">
        {gap
          ? <span className={`qy-store__dot qy-hue--${storeHue(deal.compared_retailer)}`} aria-hidden="true" />
          : <span className="qy-store__dot qy-hue--slate" aria-hidden="true" />}
        <span className="ql-row__store">{gap ? deal.compared_retailer : 'Before'}</span>
        <span className="ql-row__price" style={gap ? undefined : { textDecoration: 'line-through' }}>{formatPrice(deal.compared_price)}</span>
      </li>
    </ul>
  )
}

function DealFace({ deal }) {
  const Icon = iconFor(deal.name)
  return (
    <>
      <span className="ql-box__head">
        <span className="qy-ticon qy-ticon--md qy-hue--sky" aria-hidden="true"><Icon strokeWidth={1.6} /></span>
        <span className="qy-label">{deal.label}</span>
      </span>
      <span className="ql-box__name">{shortName(deal.name)}</span>
      <DealRows deal={deal} />
      <span className="ql-box__foot">
        <span className="qy-badge qy-badge--good">Save {formatPrice(deal.saving)}</span>
        <span className="qy-small">checked {timeAgo(deal.checked_at)}</span>
      </span>
    </>
  )
}

// The cover box: opens on load, then flips through today's real deals. The
// old deal fades out while the new one comes in, in the same spot, so the box
// never jumps or goes empty.
function PriceBox({ deals, loading }) {
  const less = usePrefersLessMotion()
  const [index, setIndex] = useState(0)
  const [leaving, setLeaving] = useState(null)
  const [paused, setPaused] = useState(false)
  const indexRef = useRef(0)
  const boxRef = useRef(null)
  const frame = useRef(0)
  const count = deals?.length ?? 0

  const next = useCallback(() => {
    if (count < 2) return
    const from = indexRef.current
    indexRef.current = (from + 1) % count
    setLeaving(less ? null : from)
    setIndex(indexRef.current)
  }, [count, less])

  useEffect(() => {
    if (leaving == null) return undefined
    const timer = setTimeout(() => setLeaving(null), 800)
    return () => clearTimeout(timer)
  }, [leaving, index])

  useEffect(() => {
    if (less || paused || count < 2) return undefined
    const timer = setInterval(next, 6500)
    return () => clearInterval(timer)
  }, [less, paused, count, next])

  // The tilt is written straight to the element once per frame, not through React.
  function lean(e) {
    if (less || e.pointerType !== 'mouse') return
    const r = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientY - r.top) / r.height - 0.5) * -6
    const y = ((e.clientX - r.left) / r.width - 0.5) * 6
    cancelAnimationFrame(frame.current)
    frame.current = requestAnimationFrame(() => {
      boxRef.current?.style.setProperty('--rx', `${x.toFixed(2)}deg`)
      boxRef.current?.style.setProperty('--ry', `${y.toFixed(2)}deg`)
    })
  }
  function settle() {
    cancelAnimationFrame(frame.current)
    boxRef.current?.style.setProperty('--rx', '0deg')
    boxRef.current?.style.setProperty('--ry', '0deg')
  }

  const deal = count ? deals[index % count] : null
  return (
    <div
      ref={boxRef}
      className="ql-box"
      onPointerMove={lean}
      onPointerEnter={() => setPaused(true)}
      onPointerLeave={() => { setPaused(false); settle() }}
      onFocus={() => setPaused(true)}
      onBlur={() => setPaused(false)}
    >
      <div className="ql-box__lid" aria-hidden="true"><span>Today's deal</span></div>
      <div className="ql-box__body">
        {loading ? (
          <div className="qy-stack" role="status" aria-label="Loading today's deals" style={{ width: '100%' }}>
            <div className="qy-skel" style={{ height: 56, width: 56, borderRadius: 16 }} />
            <div className="qy-skel" style={{ height: 20 }} />
            <div className="qy-skel" style={{ height: 96 }} />
          </div>
        ) : !deal ? (
          <div className="qy-stack" style={{ gap: 8 }}>
            <p className="qy-h3">No deals today</p>
            <p className="qy-small">No tracked price dropped enough to count. We don't fill this box with anything else.</p>
          </div>
        ) : (
          <div className="ql-box__stack">
            {leaving != null && deals[leaving] && (
              <div className="ql-box__face is-out" aria-hidden="true" key={`out-${leaving}`}><DealFace deal={deals[leaving]} /></div>
            )}
            <button
              className={`ql-box__face ql-box__deal ${leaving != null ? 'is-in' : ''}`}
              type="button"
              key={`in-${index}`}
              onClick={next}
              aria-label={`Deal ${index + 1} of ${count}: ${shortName(deal.name)}, ${formatPrice(deal.price)} at ${deal.retailer}. Show the next deal`}
            >
              <DealFace deal={deal} />
            </button>
          </div>
        )}
      </div>
      {count > 1 && (
        <div className="ql-box__dots" aria-hidden="true">
          {deals.map((d, i) => <i key={`${d.name}-${i}`} className={i === index % count ? 'on' : ''} />)}
        </div>
      )}
    </div>
  )
}

function Hud({ title, children }) {
  return (
    <section className="ql-hud">
      <p className="ql-hud__title">{title}</p>
      {children}
    </section>
  )
}

const CURVES = [0, 1, 2, 3, 4, 5].map((i) =>
  `M-80 ${120 + i * 90} C 250 ${40 + i * 95}, 450 ${260 + i * 70}, 700 ${150 + i * 85} S 1100 ${60 + i * 100}, 1290 ${180 + i * 80}`)

// The six lines behind the hero: each draws itself in, then sways slowly,
// with a short bright stretch travelling along it.
function Contours() {
  return (
    <svg className="ql-contours" viewBox="0 0 1200 700" preserveAspectRatio="none" aria-hidden="true">
      {CURVES.map((d, i) => (
        <g key={d} className="ql-curve" style={{ '--i': i }}>
          <path className="ql-curve__line" d={d} pathLength="1000" />
          <path className="ql-curve__glow" d={d} pathLength="1000" />
        </g>
      ))}
    </svg>
  )
}

// Where each tag sits in each scene, as [x %, y % of the box, rotation].
// Only transform changes between scenes, which the browser animates smoothly.
const PILE = [[4, 12, -6], [16, 29, 5], [6, 47, -3], [15, 64, 4]]

function StoryBox({ scene }) {
  const sorted = [...EXAMPLE].sort((a, b) => a.price - b.price)
  const low = sorted[0].price
  const high = sorted[sorted.length - 1].price
  const place = (tag, i) => {
    let [x, y, r] = PILE[i]
    if (scene === 1) [x, y, r] = [6, 37 + i * 15.5, 0]
    if (scene === 2) [x, y, r] = [6, 10 + sorted.indexOf(tag) * 18, 0]
    return { '--x': x, '--y': y, '--r': `${r}deg`, '--d': `${i * 80}ms` }
  }
  return (
    <div className="ql-story__box" data-scene={scene}>
      <span className="ql-story__example">Example prices</span>
      <div className={`ql-variant ${scene === 1 ? 'is-on' : ''}`} aria-hidden={scene !== 1}>
        <span className="ql-variant__keep">Phone · 8 GB / 256 GB <b>compared</b></span>
        <span className="ql-variant__drop">Phone · 8 GB / 128 GB <b>other variant</b></span>
      </div>
      {EXAMPLE.map((tag, i) => {
        const isLow = tag.price === low
        return (
          <div key={tag.store} className={`ql-tag ${scene === 2 && isLow ? 'ql-tag--low' : ''}`} style={place(tag, i)}>
            <span>{tag.store}</span>
            <span className="ql-tag__price">{formatPrice(tag.price)}</span>
            <span className={`ql-tag__extra ${scene === 2 ? 'is-on' : ''}`}>
              {isLow ? <span className="qy-badge qy-badge--good">Lowest</span> : <span className="qy-small">+ {formatPrice(tag.price - low)}</span>}
            </span>
          </div>
        )
      })}
      <div className={`ql-story__save ${scene === 2 ? 'is-on' : ''}`}>You save up to {formatPrice(high - low)}</div>
    </div>
  )
}

function Story() {
  const [scene, setScene] = useState(0)
  const refs = useRef([])
  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) setScene(Number(entry.target.dataset.scene))
      }
    }, { rootMargin: '-58% 0px -32% 0px' })
    refs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [])
  return (
    <section id="how" className="qy-wrap ql-story" aria-labelledby="how-title">
      <h2 className="qy-honeypot" id="how-title">How it works</h2>
      <div className="ql-story__stage"><StoryBox scene={scene} /></div>
      <ol className="ql-story__scenes">
        {SCENES.map(([title, body], i) => (
          <li key={title} ref={(el) => { refs.current[i] = el }} data-scene={i} className={`ql-scene ${scene === i ? 'is-on' : ''}`}>
            <span className="qy-dotnum ql-scene__n">0{i + 1}</span>
            <h3 className="qy-h1">{title}</h3>
            <p className="qy-body" style={{ fontSize: 17 }}>{body}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}

function Tickets({ deals }) {
  const track = useRef(null)
  const less = usePrefersLessMotion()
  if (!deals?.length) return null
  // One card's width plus the gap per press.
  const scroll = (direction) => {
    const card = track.current?.querySelector('.ql-ticket')
    const step = card ? card.getBoundingClientRect().width + 16 : 316
    track.current?.scrollBy({ left: direction * step, behavior: less ? 'auto' : 'smooth' })
  }
  return (
    <div className="qy-stack" style={{ gap: 16 }}>
    <ul className="ql-tickets" ref={track} tabIndex={0} aria-label="Today's deals">
      {deals.map((deal) => (
        <li key={`${deal.kind}-${deal.name}-${deal.retailer}`} className="ql-ticket">
          <div className="ql-ticket__top">
            <span className="qy-label">{deal.label}</span>
            <h3 className="ql-ticket__name" title={deal.name}>{shortName(deal.name)}</h3>
          </div>
          <div className="ql-ticket__bottom">
            <span className="qy-row" style={{ gap: 10, flexWrap: 'wrap' }}>
              <span className="qy-price qy-good" style={{ fontSize: 22 }}>{formatPrice(deal.price)}</span>
              <span className="qy-price qy-small" style={{ textDecoration: 'line-through' }}>{formatPrice(deal.compared_price)}</span>
            </span>
            <span className="qy-badge qy-badge--good" style={{ alignSelf: 'flex-start' }}>Save {formatPrice(deal.saving)}</span>
            <span className="qy-small">
              <span className="qy-store">
                <span className={`qy-store__dot qy-hue--${storeHue(deal.retailer)}`} aria-hidden="true" />{deal.retailer}
              </span>
              {deal.compared_retailer ? ` · vs ${deal.compared_retailer}` : ' · vs its earlier price'}
            </span>
          </div>
        </li>
      ))}
    </ul>
    <div className="qy-row" style={{ gap: 8 }}>
      <button className="qy-btn qy-btn--icon qy-btn--quiet" type="button" aria-label="Previous deals" onClick={() => scroll(-1)}>←</button>
      <button className="qy-btn qy-btn--icon qy-btn--quiet" type="button" aria-label="Next deals" onClick={() => scroll(1)}>→</button>
    </div>
    </div>
  )
}

export default function Landing() {
  const deals = useApi('/public/deals')
  const retailers = useApi('/retailers')
  const stores = retailers.data ?? []
  const listings = retailers.data ? stores.reduce((sum, store) => sum + store.listings, 0) : null
  const best = deals.data?.length ? [...deals.data].sort((a, b) => b.saving - a.saving)[0] : null

  return (
    <div className="ql">
      <LandingNav />
      <main>
        <section className="ql-hero">
          <Contours />
          <div className="qy-wrap">
          <div className="ql-hero__grid ql-hero__panel">
            <div className="ql-hero__copy">
              <p className="qy-label">Price comparison · Kerala</p>
              <h1 className="qy-display ql-hero__title">Every price. One yard.</h1>
              <ul className="ql-facts">
                <li>Kerala stores, side by side</li>
                <li>{stores.length || 4} stores, checked every day</li>
                <li>Only prices the stores publish</li>
              </ul>
              <div className="qy-row" style={{ flexWrap: 'wrap' }}>
                <Link className="qy-btn qy-btn--primary" to="/signup">Sign up free <ArrowRight size={16} aria-hidden="true" /></Link>
                <Link className="qy-btn" to="/login">Log in</Link>
              </div>
            </div>
            <PriceBox deals={deals.data} loading={deals.loading} />
            <div className="ql-hero__hud">
              <Hud title="Biggest saving today">
                {best ? (
                  <>
                    <p className="ql-hud__big qy-good">{formatPrice(best.saving)}</p>
                    <p className="qy-small ql-hud__line">{shortName(best.name)}</p>
                  </>
                ) : <p className="qy-small">No deals today</p>}
              </Hud>
              <Hud title="Coverage">
                <div className="ql-hud__stats">
                  <span><b className="ql-hud__big"><CountUp value={retailers.data ? stores.length : null} /></b>stores</span>
                  <span><b className="ql-hud__big"><CountUp value={listings} /></b>listings</span>
                </div>
              </Hud>
            </div>
          </div>
          </div>
          <a className="ql-scroll" href="#how">See how it works <span aria-hidden="true">↓</span></a>
        </section>

        <Story />

        <section id="deals" className="qy-wrap qy-section" aria-labelledby="deals-title">
          <div className="qy-between" style={{ marginBottom: 24 }}>
            <div className="qy-stack" style={{ gap: 4 }}>
              <p className="qy-label">Calculated from recorded prices</p>
              <h2 className="qy-h1" id="deals-title">Today's deals</h2>
            </div>
            <p className="qy-small" style={{ maxWidth: '44ch' }}>
              A real recorded price drop, or a clear gap between stores. Never measured against an MRP.
            </p>
          </div>
          {deals.error ? (
            <div className="qy-empty" role="alert">
              <p className="qy-small">We couldn't load today's deals.</p>
              <button className="qy-btn" type="button" onClick={deals.retry}>Try again</button>
            </div>
          ) : deals.data && !deals.data.length ? (
            <div className="qy-empty"><p className="qy-small">No deals today. We don't fill this space with anything else.</p></div>
          ) : <Tickets deals={deals.data} />}
        </section>

        <section id="stores" className="qy-wrap qy-section" aria-labelledby="stores-title" style={{ paddingTop: 0 }}>
          <h2 className="qy-h1" id="stores-title" style={{ marginBottom: 24 }}>Stores we compare</h2>
          {retailers.error ? (
            <div className="qy-empty" role="alert">
              <p className="qy-small">We couldn't load the store list.</p>
              <button className="qy-btn" type="button" onClick={retailers.retry}>Try again</button>
            </div>
          ) : (
            <ul className="qy-grid-4" style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {stores.map((store) => (
                <li key={store.id} className={`qy-tile ql-store qy-hue--${storeHue(store.name)}`}>
                  <span className="ql-store__dot" aria-hidden="true" />
                  <span className="qy-stack" style={{ gap: 0, minWidth: 0 }}>
                    <span style={{ fontWeight: 600 }}>{store.name}</span>
                    <span className="qy-small">{formatCount(store.listings)} listings</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="qy-wrap" style={{ paddingBottom: 64 }}>
          <div className="qy-hero-band ql-final">
            <h2 className="qy-display ql-final__title">Find your price.</h2>
            <p className="qy-body">Free to use. Sign up with your email and see every store's price side by side.</p>
            <Link className="qy-btn qy-btn--primary" to="/signup">Sign up free <ArrowRight size={16} aria-hidden="true" /></Link>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}
