import { useEffect, useState } from 'react'

const KEY = 'qy-theme'

function stored() {
  try {
    return localStorage.getItem(KEY) === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

export function useTheme() {
  const [theme, setTheme] = useState(stored)
  useEffect(() => {
    document.documentElement.classList.toggle('qy--dark', theme === 'dark')
    try {
      localStorage.setItem(KEY, theme)
    } catch {
      // storage unavailable: the choice lasts until the page closes
    }
  }, [theme])
  return [theme, setTheme]
}
