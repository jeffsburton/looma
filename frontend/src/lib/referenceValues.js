import api from './api'

// Simple per-session cache for reference values
// Uses both in-memory Map (fast) and sessionStorage (persist across page reloads in same browser session)
const memCache = new Map() // key: code (uppercased), value: Promise resolving to array of values

const STORAGE_KEY_PREFIX = 'refvals:'

function storageKey(code) {
  return `${STORAGE_KEY_PREFIX}${(code || '').toUpperCase()}`
}

function getFromSession(code) {
  try {
    const key = storageKey(code)
    const raw = typeof window !== 'undefined' ? window.sessionStorage?.getItem(key) : null
    if (!raw) return null
    return JSON.parse(raw)
  } catch (_) {
    return null
  }
}

function setToSession(code, data) {
  try {
    const key = storageKey(code)
    if (typeof window !== 'undefined') {
      window.sessionStorage?.setItem(key, JSON.stringify(data))
    }
  } catch (_) { /* ignore */ }
}

export function invalidateReferenceValues(code) {
  const key = (code || '').toUpperCase()
  memCache.delete(key)
  try {
    if (typeof window !== 'undefined') {
      window.sessionStorage?.removeItem(storageKey(code))
    }
  } catch (_) { /* ignore */ }
}

export async function getReferenceValues(code) {
  if (!code) return []
  const key = (code || '').toUpperCase()

  // If a pending or fulfilled promise is cached in memory, return it
  const cached = memCache.get(key)
  if (cached) return cached

  // Otherwise, attempt to hydrate from sessionStorage synchronously
  const fromSession = getFromSession(code)
  if (Array.isArray(fromSession)) {
    const p = Promise.resolve(fromSession)
    memCache.set(key, p)
    return p
  }

  // Create a single-flight promise to fetch and populate caches
  const p = api.get(`/api/v1/reference/${encodeURIComponent(code)}/values`)
    .then(res => {
      const data = Array.isArray(res.data) ? res.data : []
      setToSession(code, data)
      return data
    })
    .catch(err => {
      // On error, clear memory entry to allow retry later
      memCache.delete(key)
      throw err
    })

  memCache.set(key, p)
  return p
}
