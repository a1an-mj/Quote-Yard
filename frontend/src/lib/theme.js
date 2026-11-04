import { useEffect, useState } from 'react'
import { canAnimate, circle } from './motion'

const KEY = 'qy-theme'

function stored() {
  try {
    return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

const lessMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

function paint(theme) {
  document.documentElement.classList.toggle('qy--dark', theme === 'dark')
}

// Switching theme doesn't snap: with view transitions the new theme grows in
// a circle from the switch (or crossfades when there is no click point);
// other browsers ease the colours. Per-element transitions are paused
// meanwhile, so nothing animates twice.
const THEME_MS = 650

function paintSmoothly(theme, from) {
  const root = document.documentElement
  if (lessMotion()) return paint(theme)
  root.classList.add('qy-theming')
  const done = () => root.classList.remove('qy-theming')
  if (from && canAnimate()) {
    circle('open', from.x, from.y, () => paint(theme), { ms: THEME_MS, hover: false }).finished.finally(done)
  } else if (document.startViewTransition) {
    document.startViewTransition(() => paint(theme)).finished.finally(done)
  } else {
    root.classList.add('qy-theme-fade')
    paint(theme)
    setTimeout(() => { root.classList.remove('qy-theme-fade'); done() }, 450)
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(stored)

  useEffect(() => {
    paint(theme) // the first render, and other tabs' choices, without a fade
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function choose(next, from) {
    if (next === theme) return
    paintSmoothly(next, from)
    setTheme(next)
    try {
      localStorage.setItem(KEY, next)
    } catch {
      // storage unavailable: the choice lasts until the page closes
    }
  }
  return [theme, choose]
}
