import axios from 'axios'
import { getCookie } from './cookies'
import { showServerError } from './serverErrorStore'
import { clearPermissions } from './permissions'
import router from '../router'

// Resolve API base URL:
// Priority (production):
// 1) Runtime global (window.__LOOMA_API_URL or window.__APP_CONFIG__.apiBaseUrl) for static hosts without rebuilds
// 2) Fallback to same-origin ('/') which works with dev proxy or when backend serves under the same host
// Priority (development only):
// - Same as above, but also allow build-time env (VITE_API_BASE or VITE_LOOMA_API_URL) to ease local testing
const runtimeApiBase = (typeof window !== 'undefined')
  ? (window.__LOOMA_API_URL || (window.__APP_CONFIG__ && window.__APP_CONFIG__.apiBaseUrl))
  : undefined

const buildEnvApiBase = import.meta.env?.VITE_API_BASE || import.meta.env?.VITE_LOOMA_API_URL
const isDev = !!(import.meta.env && (import.meta.env.DEV || import.meta.env.MODE === 'development'))

// In production, ignore build-time env to ensure same-origin by default.
const effectiveApiBase = runtimeApiBase || (isDev ? buildEnvApiBase : '')
const apiBase = (effectiveApiBase || '').toString().trim()

const api = axios.create({
    baseURL: apiBase || '/', // if not configured, default to same-origin; dev proxy will handle /api
    withCredentials: true, // send and receive cookies (required for HttpOnly session cookies)
})

// Attach token from secure cookie if present and add CSRF header for mutating requests (if available)
api.interceptors.request.use((config) => {
    const token = getCookie('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`

    try {
        const method = (config.method || 'get').toUpperCase()
        if (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE') {
            const csrf = getCookie('csrf_token')
            if (csrf) {
                config.headers['X-CSRF-Token'] = csrf
            }
        }
    } catch (_) { /* noop */ }

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
                    clearPermissions()
                } catch (_) { /* noop */ }

                // Redirect to login with return URL when unauthorized
                try {
                    const current = router?.currentRoute?.value
                    const currentPath = current?.fullPath || '/'
                    const isOnCase = typeof current?.path === 'string' && current.path.startsWith('/cases')
                    const message = isOnCase ? 'Please log in to view that case.' : 'Please log in to view that page.'
                    if (current?.name !== 'login') {
                        router.push({ name: 'login', query: { redirect: currentPath, message } })
                    }
                } catch (_) { /* noop */ }
            }

            if (status === 403) {
                const data = res.data || {}
                const detail = data.detail ?? 'Forbidden'
                // Provide a clearer message for CSRF failures
                const isCsrf = typeof detail === 'string' && /csrf/i.test(detail)
                const message = isCsrf
                    ? 'Security check failed (CSRF). Please refresh the page and try again.'
                    : 'Access denied. You do not have permission to perform this action.'
                const details = {
                    detail,
                    path: data.path ?? res.config?.url ?? '',
                    method: data.method ?? res.config?.method?.toUpperCase?.() ?? '',
                    status: 403
                }
                showServerError({ message, details })

                // If user is on a case URL and hit 403 likely due to auth/session issues, redirect to login with return URL
                try {
                    const current = router?.currentRoute?.value
                    const currentPath = current?.fullPath || '/'
                    const isOnCase = typeof current?.path === 'string' && current.path.startsWith('/cases')
                    if (isOnCase && current?.name !== 'login') {
                        if (typeof window !== 'undefined') {
                            window.localStorage?.removeItem('is_authenticated')
                        }
                        clearPermissions()
                        const message = 'Please log in to view that case.'
                        router.push({ name: 'login', query: { redirect: currentPath, message } })
                    }
                } catch (_) { /* noop */ }
            }

            if (status === 419) {
                    const message = 'Your session has expired. You are required login again.'

                    // Notify app to show toast
                    if (typeof window !== 'undefined' && window.dispatchEvent) {
                        window.dispatchEvent(new CustomEvent('app:toast', {
                            detail: {
                                severity: 'warn',
                                summary: 'Session Expired',
                                detail: message,
                                life: 5000
                            }
                        }))
                    }

                    // Clear auth hints and redirect to login with return URL
                    try {
                        if (typeof window !== 'undefined') {
                            window.localStorage?.removeItem('is_authenticated')
                        }
                        clearPermissions()
                    } catch (_) { /* noop */ }

                    try {
                        const current = router?.currentRoute?.value
                        const currentPath = current?.fullPath || '/'
                        const message = 'Your session has expired. Please log in to continue.'
                        if (current?.name !== 'login') {
                            router.push({ name: 'login', query: { redirect: currentPath, message } })
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
