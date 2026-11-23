import axios from 'axios'
import Cookies from 'js-cookie'

// All requests go to /api (Vite proxies them to Django, see vite.config.js)
const api = axios.create({ baseURL: '/api' })

// Django protects unsafe requests with a CSRF token that lives in a cookie
api.interceptors.request.use((config) => {
  const token = Cookies.get('csrftoken')
  if (token) config.headers['X-CSRFToken'] = token
  return config
})

// The session expired -> let the app send the user to the login page
let onUnauthorized = () => {}
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const res = error.response
    const url = error.config?.url || ''
    if (res && [401, 403].includes(res.status) && !url.startsWith('/auth/') && !url.startsWith('/users/')) {
      if (res.data?.detail?.includes?.('credentials')) onUnauthorized()
    }
    return Promise.reject(error)
  },
)

// Turn a DRF error response into one readable line
export function formatError(error) {
  const data = error?.response?.data
  if (!data) return error?.message || 'Something went wrong'
  if (typeof data === 'string') return 'Server error'
  if (data.detail) return data.detail
  return Object.entries(data)
    .map(([field, msgs]) => `${field}: ${[].concat(msgs).join(' ')}`)
    .join('; ')
}

export default api
