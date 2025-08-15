import { useEffect } from 'react'
import { useAuthStore } from '@/features/auth/store'
import { authApi } from '@/features/auth/api'

// Module-level flag — only bootstrap once per page load
let bootstrapped = false

export function useAuth() {
  const { user, isAuthenticated, isLoading, setUser, setLoading } = useAuthStore()

  useEffect(() => {
    if (bootstrapped) return
    bootstrapped = true

    setLoading(true)
    authApi
      .me()
      .then(({ data }) => setUser(data))
      .catch(() => setUser(null))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { user, isAuthenticated, isLoading }
}
