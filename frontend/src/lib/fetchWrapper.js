import api from './api'

// Create a minimal Response-like object to emulate fetch API behavior
function makeResponseLike(axiosResponse) {
    const status = axiosResponse?.status ?? 0
    const statusText = axiosResponse?.statusText ?? ''
    const headersRaw = axiosResponse?.headers || {}
    const data = axiosResponse?.data

    const headers = {
        get(name) {
            if (!name) return undefined
            const key = String(name).toLowerCase()
            return headersRaw[key]
        }
    }

    return {
        ok: status >= 200 && status < 300,
        status,
        statusText,
        url: axiosResponse?.config?.url || '',
        headers,
        // Return JSON (axios already parsed JSON by default)
        async json() {
            return data
        },
        // If axios gave us text, return it; otherwise stringify
        async text() {
            if (typeof data === 'string') return data
            try { return JSON.stringify(data) } catch { return String(data) }
        },
        // Ensure Blob is returned for binary responses
        async blob() {
            if (data instanceof Blob) return data
            // Try to construct a Blob from ArrayBuffer or object
            if (data instanceof ArrayBuffer) return new Blob([data])
            if (data && data.byteLength && typeof data.slice === 'function') {
                try { return new Blob([data]) } catch { /* ignore */ }
            }
            // Fallback: string-ify
            const txt = typeof data === 'string' ? data : (function () { try { return JSON.stringify(data) } catch { return '' } })()
            return new Blob([txt], { type: headers.get('content-type') || 'application/octet-stream' })
        }
    }
}

// Map fetch init/options to axios config
function toAxiosConfig(input, init = {}) {
    const url = typeof input === 'string' ? input : (input && input.url ? input.url : String(input))
    const method = (init.method || 'GET').toLowerCase()
    const headers = init.headers || {}
    const credentials = init.credentials // 'omit' | 'same-origin' | 'include'

    let data = init.body
    // If body is a plain object and content-type JSON is implied in many places, keep as-is; axios will JSON.stringify when header is set.
    // For FormData, Blob, etc., axios will handle appropriately.

    // Try to infer responseType for blobs
    let responseType
    const accept = (headers && (headers['Accept'] || headers['accept'])) || ''
    if (init.responseType) {
        responseType = init.responseType
    } else if (typeof accept === 'string' && /(^|,|\s)(application\/octet-stream|image\/|video\/|audio\/|application\/pdf)/i.test(accept)) {
        responseType = 'blob'
    }

    const config = {
        url,
        method,
        headers,
        data,
        withCredentials: credentials === 'include' ? true : (credentials === 'omit' ? false : api.defaults.withCredentials),
        signal: init.signal,
        responseType,
    }

    return config
}

export function installGlobalFetch() {
    if (typeof window === 'undefined') return
    // Preserve original fetch in case we need it for non-API same-origin assets
    const originalFetch = window.fetch?.bind(window)

    window.fetch = async function (input, init) {
        try {
            const config = toAxiosConfig(input, init)
            const res = await api.request(config)
            return makeResponseLike(res)
        } catch (err) {
            // Ensure axios interceptors (including error handler) have run.
            // Emulate fetch behavior: fetch resolves for HTTP errors, rejects only on network failures.
            const res = err && err.response
            if (res) {
                return makeResponseLike(res)
            }
            // Network error: emulate a rejected fetch Promise
            // If desired, we could return a Response-like with ok=false, but fetch actually rejects on network failure.
            throw err
        }
    }

    // Provide a way to use the original fetch if needed
    window.__originalFetch = originalFetch
}
