import { useEffect, useState } from 'react'

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

// Switching theme fades the whole page across instead of snapping. Browsers
// with view transitions crossfade a snapshot (cheap); others ease the colours.
// Per-element transitions are paused meanwhile, so nothing animates twice.
function paintSmoothly(theme) {
  const root = document.documentElement
  if (lessMotion()) return paint(theme)
  root.classList.add('qy-theming')
  const done = () => root.classList.remove('qy-theming')
  if (document.startViewTransition) {
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

  function choose(next) {
    if (next === theme) return
    paintSmoothly(next)
    setTheme(next)
    try {
      localStorage.setItem(KEY, next)
    } catch {
      // storage unavailable: the choice lasts until the page closes
    }
  }
  return [theme, choose]
}
