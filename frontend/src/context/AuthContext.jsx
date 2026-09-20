import { createContext, useContext, useEffect, useState } from 'react'

const AuthContext = createContext(null)
const STORAGE_KEY = 'quoteyard_mock_user'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) setUser(JSON.parse(stored))
    } catch {
      // ignore corrupted storage
    }
    setIsLoading(false)
  }, [])

  function persist(nextUser) {
    setUser(nextUser)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser))
    } catch {
      // storage unavailable, continue with in-memory state
    }
  }

  // This is a prototype only — there is no real backend or authentication.
  function signup({ fullName, email }) {
    const mockUser = { name: fullName || 'there', email, method: 'email' }
    persist(mockUser)
    return mockUser
  }

  function login({ email }) {
    const namePart = email.split('@')[0] || 'there'
    const displayName = namePart.charAt(0).toUpperCase() + namePart.slice(1)
    const mockUser = { name: displayName, email, method: 'email' }
    persist(mockUser)
    return mockUser
  }

  function loginWithGoogle() {
    const mockUser = {
      name: 'Anjali Menon',
      email: 'anjali.menon@gmail.com',
      method: 'google',
    }
    persist(mockUser)
    return mockUser
  }

  function logout() {
    setUser(null)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, signup, login, loginWithGoogle, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
