import axios from 'axios'
import { getCookie } from './cookies'
import { showServerError } from './serverErrorStore'

// Resolve API base URL:
// Priority:
// 1) Runtime global (window.__LOOMA_API_URL or window.__APP_CONFIG__.apiBaseUrl) for static hosts without rebuilds
// 2) Build-time env (VITE_API_BASE or VITE_LOOMA_API_URL)
// 3) Fallback to same-origin ('/') which works with dev proxy or when backend serves under the same host
const runtimeApiBase = (typeof window !== 'undefined')
  ? (window.__LOOMA_API_URL || (window.__APP_CONFIG__ && window.__APP_CONFIG__.apiBaseUrl))
  : undefined

const buildEnvApiBase = import.meta.env?.VITE_API_BASE || import.meta.env?.VITE_LOOMA_API_URL

const apiBase = (runtimeApiBase || buildEnvApiBase || '').toString().trim()

const api = axios.create({
    baseURL: apiBase || '/', // if not configured, default to same-origin; dev proxy will handle /api
    withCredentials: true, // send and receive cookies (required for HttpOnly session cookies)
})

// Attach token from secure cookie if present
api.interceptors.request.use((config) => {
    const token = getCookie('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

// Global response error handling for server errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        try {
            const res = error?.response
            // Network or CORS errors (no response)
            if (!res) {
                showServerError({
                    message: 'Network error: Unable to reach the server.',
                    details: {
                        detail: 'Network Error',
                        error: error?.message || 'Network/Connection issue',
                        error_type: error?.name || 'NetworkError'
                    }
                })
                return Promise.reject(error)
            }

            const status = res.status

            // Keep UI auth state in sync: if unauthorized, clear client-side auth hint
            if (status === 401) {
                try {
                    if (typeof window !== 'undefined') {
                        window.localStorage?.removeItem('is_authenticated')
                    }
                } catch (_) { /* noop */ }
            }

            if (status === 500) {
                const data = res.data || {}
                // Prefer provided fields per backend contract
                const errorId = data.error_id || res.headers?.['x-error-id'] || res.headers?.['X-Error-ID']
                const message = 'A server error occurred. Our team has been notified.'
                const details = {
                    detail: data.detail ?? 'Internal Server Error',
                    error: data.error ?? '',
                    error_type: data.error_type ?? '',
                    trace: data.trace ?? '',
                    error_id: errorId ?? '',
                    path: data.path ?? res.config?.url ?? '',
                    method: data.method ?? res.config?.method?.toUpperCase?.() ?? ''
                }
                showServerError({ message, details })
            }
        } catch (e) {
            // Ensure we never block propagation on unexpected issues in handler
            console.error('Global error handler failed:', e)
        }
        return Promise.reject(error)
    }
)

export default api
