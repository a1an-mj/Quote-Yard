import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

// Loads a GET path. Returns { data, error, loading, retry }.
//
// Data from an earlier path is never returned for a new one: a page that
// switches from products to listings would otherwise draw the old products
// with the listing layout for a moment, and crash.
export function useApi(path) {
  const [state, setState] = useState({ path, data: null, error: null, loading: true })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    // A retry of the same path keeps showing what is there; a new path starts empty.
    setState((s) => (s.path === path
      ? { ...s, error: null, loading: true }
      : { path, data: null, error: null, loading: true }))
    api(path, { signal: controller.signal })
      .then((data) => setState({ path, data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ path, data: null, error, loading: false })
      })
    return () => controller.abort()
  }, [path, attempt])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])
  if (state.path !== path) return { data: null, error: null, loading: true, retry }
  const { data, error, loading } = state
  return { data, error, loading, retry }
}
