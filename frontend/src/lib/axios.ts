import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// ---------------------------------------------------------------------------
// Response interceptor — on 401 attempt one silent token refresh
// ---------------------------------------------------------------------------

let isRefreshing = false
let refreshQueue: Array<(token: void) => void> = []

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config

    if (error.response?.status === 401 && !original._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshQueue.push(() => resolve(api(original)))
        })
      }

      original._retry = true
      isRefreshing = true

      try {
        await api.post('/auth/refresh')
        refreshQueue.forEach((cb) => cb())
        refreshQueue = []
        return api(original)
      } catch {
        refreshQueue = []
        // Redirect to login — let the auth store handle clearing state
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  }
)

export default api
