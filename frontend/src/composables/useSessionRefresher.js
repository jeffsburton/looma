import api from '@/lib/api'
import { getCookie } from '@/lib/cookies'

function decodeJwtExp(token) {
  try {
    const payload = token.split('.')[1]
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    const obj = JSON.parse(json)
    return typeof obj.exp === 'number' ? obj.exp : null
  } catch {
    return null
  }
}

function nowSec() { return Math.floor(Date.now() / 1000) }

export function useSessionRefresher(options = {}) {
  const intervalMs = options.intervalMs ?? 60_000           // check every 60s
  const activeWindowMs = options.activeWindowMs ?? 5 * 60_000 // consider active if input in last 5 min
  const minBetweenRefreshMs = options.minBetweenRefreshMs ?? 5 * 60_000 // throttle: 5 min
  const refreshWhenExpInMin = options.refreshWhenExpInMin ?? 10 // refresh if exp within 10 min
  const authCookieName = options.authCookieName ?? 'access_token'

  let lastActivityAt = Date.now()
  let lastRefreshAt = 0
  let timer = null
  let isDestroyed = false

  // Multi-tab coordination
  let bc = null
  try { if (typeof window !== 'undefined' && 'BroadcastChannel' in window) bc = new BroadcastChannel('auth') } catch {}
  const LS_REFRESH_IN_FLIGHT = 'auth_refresh_in_flight_at'
  const LS_LAST_REFRESH_AT = 'auth_last_refresh_at'

  const markRefreshInFlight = () => {
    try { localStorage.setItem(LS_REFRESH_IN_FLIGHT, String(Date.now())) } catch {}
  }
  const clearRefreshInFlight = () => {
    try { localStorage.removeItem(LS_REFRESH_IN_FLIGHT) } catch {}
  }
  const isRecentlyInFlight = (ms = 15_000) => {
    try {
      const v = parseInt(localStorage.getItem(LS_REFRESH_IN_FLIGHT) || '0', 10)
      return v && (Date.now() - v) < ms
    } catch {
      return false
    }
  }

  const publishRefreshed = () => {
    const at = Date.now()
    try { localStorage.setItem(LS_LAST_REFRESH_AT, String(at)) } catch {}
    if (bc) { try { bc.postMessage({ type: 'refreshed', at }) } catch {} }
  }

  const onActivity = () => { lastActivityAt = Date.now() }

  function handleVisibilityChange() {
    if (document.visibilityState === 'visible') {
      const minLeft = minutesUntilExp()
      const longSince = (Date.now() - lastRefreshAt) >= minBetweenRefreshMs
      const expClose = minLeft !== null ? (minLeft <= refreshWhenExpInMin) : false
      if (longSince || expClose) refresh()
    }
  }

  const addActivityListeners = () => {
    const evs = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll']
    evs.forEach((ev) => window.addEventListener(ev, onActivity, { passive: true }))
    document.addEventListener('visibilitychange', handleVisibilityChange, { passive: true })

    if (bc) {
      bc.onmessage = (e) => {
        if (e?.data?.type === 'refreshed') {
          lastRefreshAt = e.data.at || Date.now()
        }
      }
    } else {
      window.addEventListener('storage', (e) => {
        if (e.key === LS_LAST_REFRESH_AT && e.newValue) {
          lastRefreshAt = parseInt(e.newValue, 10) || Date.now()
        }
      })
    }
  }

  const removeActivityListeners = () => {
    const evs = ['mousemove', 'mousedown', 'keydown', 'wheel', 'touchstart', 'scroll']
    evs.forEach((ev) => window.removeEventListener(ev, onActivity))
    document.removeEventListener('visibilitychange', handleVisibilityChange)
    if (bc) { try { bc.close() } catch {} bc = null }
  }

  const minutesUntilExp = () => {
    const token = getCookie(authCookieName)
    if (!token) return null
    const exp = decodeJwtExp(token) // seconds since epoch
    if (!exp) return null
    const deltaSec = exp - nowSec()
    return deltaSec / 60
  }

  const shouldRefreshNow = () => {
    if (Date.now() - lastRefreshAt < minBetweenRefreshMs) return false
    const recentActivity = (Date.now() - lastActivityAt) <= activeWindowMs
    if (!recentActivity) return false

    const minLeft = minutesUntilExp()
    // If we cannot read the cookie/JWT exp (e.g., HttpOnly), fall back to time-based refresh while active
    if (minLeft === null) return true
    return minLeft <= refreshWhenExpInMin
  }

  async function refresh() {
    if (isRecentlyInFlight()) return
    markRefreshInFlight()
    try {
      await api.post('/api/v1/auth/refresh')
      lastRefreshAt = Date.now()
      publishRefreshed()
    } catch (_) {
      // 401/419 are handled by interceptors (toast + redirect)
    } finally {
      clearRefreshInFlight()
    }
  }

  function tick() {
    if (isDestroyed) return
    if (shouldRefreshNow()) refresh()
  }

  function start() {
    addActivityListeners()
    lastActivityAt = Date.now()
    try { lastRefreshAt = parseInt(localStorage.getItem(LS_LAST_REFRESH_AT) || '0', 10) || 0 } catch { lastRefreshAt = 0 }
    if (!timer) timer = setInterval(tick, intervalMs)
  }

  function stop() {
    isDestroyed = true
    if (timer) { clearInterval(timer); timer = null }
    removeActivityListeners()
  }

  return { start, stop }
}
