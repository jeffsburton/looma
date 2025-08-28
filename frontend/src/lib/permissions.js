// Simple client-side permissions cache.
// Stores permission codes returned by the backend login endpoint.
// This is for UI gating only; server remains the source of truth.

const STORAGE_KEY = 'permission_codes'

let _codes = []

function _loadFromStorage() {
  try {
    const raw = typeof window !== 'undefined' ? window.localStorage?.getItem(STORAGE_KEY) : null
    if (!raw) return []
    const parsed = JSON.parse(raw)
    if (Array.isArray(parsed)) {
      // Normalize to unique strings
      const unique = Array.from(new Set(parsed.filter((v) => typeof v === 'string')))
      return unique
    }
  } catch (_) { /* noop */ }
  return []
}

function _saveToStorage(codes) {
  try {
    if (typeof window !== 'undefined') {
      if (codes && codes.length) {
        window.localStorage?.setItem(STORAGE_KEY, JSON.stringify(codes))
      } else {
        window.localStorage?.removeItem(STORAGE_KEY)
      }
    }
  } catch (_) { /* noop */ }
}

// Initialize from storage
_codes = _loadFromStorage()

export function setPermissions(codes) {

  if (!Array.isArray(codes)) {
    _codes = []
    _saveToStorage(_codes)
    return
  }
  // Normalize: keep only non-empty strings, unique, preserve order
  const seen = new Set()
  const norm = []
  for (const c of codes) {
    if (typeof c !== 'string' || !c.trim()) continue
    const t = c.trim()
    if (!seen.has(t)) { seen.add(t); norm.push(t) }
  }
  _codes = norm
  _saveToStorage(_codes)
}

export function clearPermissions() {
  _codes = []
  _saveToStorage(_codes)
}

export function getPermissions() {
  return [..._codes]
}

export function hasPermission(code) {
  if (typeof code !== 'string' || !code) return false
  return _codes.includes(code)
}

export function hasAny(codes) {
  if (!Array.isArray(codes) || !codes.length) return false
  for (const c of codes) {
    if (typeof c === 'string' && _codes.includes(c)) return true
  }
  return false
}
