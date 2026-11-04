import { flushSync } from 'react-dom'
import { Link, useNavigate } from 'react-router-dom'

// The site's few big page moves, all made with view transitions:
//  - circle: Log in / Sign up, logging in to Home and the theme switch grow
//    from where you clicked; Back shrinks the circle to where it came from.
//  - search: Home's big search box flies into the Results top bar, and back.
// Browsers without view transitions, and visitors who ask for less motion,
// get the normal instant change.

const lessMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
export const canAnimate = () => typeof document !== 'undefined' && !!document.startViewTransition && !lessMotion()

const OPEN_MS = 900
const CLOSE_MS = 700

// The browser shows a snapshot of the new page while the circle plays, and a
// snapshot has no hover. So the button now under the mouse wears its hover
// look from the start, until the mouse moves and the real hover takes over;
// otherwise its glow pops on just after the circle ends.
function keepHover(x, y) {
  // elementFromPoint answers <html> during a view transition, so look by position.
  const el = [...document.querySelectorAll('a.qy-btn, button.qy-btn')].find((b) => {
    const r = b.getBoundingClientRect()
    return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
  })
  if (!el) return () => {}
  // At once, not faded in, or it flashes white inside the small starting circle.
  el.style.transition = 'none'
  el.classList.add('qy-hovered')
  return () => {
    el.style.transition = ''
    window.addEventListener('pointermove', () => el.classList.remove('qy-hovered'), { once: true })
  }
}

// kind 'open' grows the new screen from (x, y); 'close' shrinks the old one into it.
export function circle(kind, x, y, update, { ms, hover = kind === 'open' } = {}) {
  const root = document.documentElement
  root.dataset.qyCircle = kind
  let release = () => {}
  const t = document.startViewTransition(() => {
    flushSync(update)
    if (hover) release = keepHover(x, y)
  })
  t.ready.then(() => {
    const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
    const frames = [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`]
    root.animate(
      { clipPath: kind === 'open' ? frames : frames.reverse() },
      {
        duration: ms ?? (kind === 'open' ? OPEN_MS : CLOSE_MS),
        easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
        fill: 'forwards', // hold the last frame until the snapshots go away
        pseudoElement: kind === 'open' ? '::view-transition-new(root)' : '::view-transition-old(root)',
      },
    )
  }).catch(() => {})
  t.finished.finally(() => { delete root.dataset.qyCircle; release() })
  return t
}

// The middle of an element, for keyboard presses and form buttons.
export function middleOf(el) {
  const b = el.getBoundingClientRect()
  return { x: b.left + b.width / 2, y: b.top + b.height / 2 }
}

// Where a click happened, or the element's middle for a keyboard press.
export function originOf(e) {
  return e.detail > 0 ? { x: e.clientX, y: e.clientY } : middleOf(e.currentTarget)
}

// Go to a page with the circle. With a point saved in history, Back shrinks it
// again; a replaced page (logging in) has nothing to go back to, so none is saved.
export function circleTo(navigate, to, { x, y }, { replace = false } = {}) {
  if (!canAnimate()) return navigate(to, { replace })
  // Kept as fractions of the window, so Back still lands right after a resize.
  const state = replace ? undefined : { qyCircle: { x: x / innerWidth, y: y / innerHeight } }
  circle('open', x, y, () => {
    navigate(to, { replace, state })
    window.scrollTo(0, 0)
  })
}

export function CircleLink({ to, onClick, ...rest }) {
  const navigate = useNavigate()
  function click(e) {
    onClick?.(e)
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || !canAnimate()) return
    e.preventDefault()
    circleTo(navigate, to, originOf(e))
  }
  return <Link to={to} onClick={click} {...rest} />
}

// ---- Search box: Home's big box flies into the Results top bar
function flySearch(update) {
  const root = document.documentElement
  root.dataset.qyMorph = 'search'
  const t = document.startViewTransition(() => flushSync(update))
  t.finished.finally(() => { delete root.dataset.qyMorph })
}

export function searchTo(navigate, to) {
  const go = () => {
    navigate(to, { state: { qySearch: true } })
    window.scrollTo(0, 0)
  }
  if (canAnimate()) flySearch(go)
  else go()
}

// ---- Back and Forward
// The page on screen: its place in history and how it was opened.
let here = null
function entry() {
  const s = window.history.state
  return { idx: s?.idx ?? 0, circle: s?.usr?.qyCircle, search: s?.usr?.qySearch }
}
export function noteEntry() {
  here = entry()
}

// Runs before the router hears about Back/Forward (added first, capture phase).
// When a move should play, the router is told inside the transition instead.
let replaying = false
function tellRouter() {
  replaying = true
  try {
    window.dispatchEvent(new PopStateEvent('popstate', { state: window.history.state }))
  } finally {
    replaying = false
  }
}
if (typeof window !== 'undefined') {
  window.addEventListener('popstate', (e) => {
    if (replaying || !here || !canAnimate()) return
    const next = entry()
    const back = next.idx < here.idx
    const forward = next.idx > here.idx
    // Back undoes how the page we leave was opened; Forward replays how the next one was.
    const how = back ? here : forward ? next : null
    if (how?.circle) {
      e.stopImmediatePropagation()
      circle(back ? 'close' : 'open', how.circle.x * innerWidth, how.circle.y * innerHeight, tellRouter)
    } else if (how?.search) {
      e.stopImmediatePropagation()
      flySearch(tellRouter)
    }
  }, true)
}
