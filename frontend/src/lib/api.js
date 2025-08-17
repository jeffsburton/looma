import axios from 'axios'
import { getCookie } from './cookies'
import { showServerError } from './serverErrorStore'

const api = axios.create({
    baseURL: '/', // Vite proxy sends /api to FastAPI
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
