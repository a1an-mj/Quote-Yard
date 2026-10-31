import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

// Loads a GET path. Returns { data, error, loading, retry }.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setState((s) => ({ ...s, error: null, loading: true }))
    api(path, { signal: controller.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false })
      })
    return () => controller.abort()
  }, [path, attempt])

  const retry = useCallback(() => setAttempt((n) => n + 1), [])
  return { ...state, retry }
}
