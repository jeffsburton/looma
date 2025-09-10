import { ref } from 'vue'
import api from '@/lib/api'
import { getCookie } from '@/lib/cookies'
import router from '@/router'

import { createClientLogger } from '@/lib/util'
const log = createClientLogger('WebSockets')

// Global reactive map of counts keyed as specified, e.g.,
// count, count_rfis, count_<enc_case_id>, count_rfis_<enc_case_id>, ...
export const gMessageCounts = ref({})
// Global event bus for message-related websocket events
export const gMessageEvents = (typeof window !== 'undefined' && typeof window.EventTarget !== 'undefined') ? new EventTarget() : {
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent() { return false },
}

let _ws = null
let _connecting = false
let _inited = false
let _encUserId = null
let _sessionId = null
let _reconnectTimer = null
let _reconnectAttempts = 0
let _initRetryTimer = null
let _shouldReconnect = true

function parseJwtJti(token) {
  try {
    const parts = String(token || '').split('.')
    if (parts.length < 2) return null
    const payload = JSON.parse(decodeURIComponent(escape(window.atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))))
    return payload?.jti || null
  } catch { return null }
}

function getWsUrl(encUid, sid) {
  try {
    const runtimeBase = (typeof window !== 'undefined') ? (window.__LOOMA_API_URL || (window.__APP_CONFIG__ && window.__APP_CONFIG__.apiBaseUrl) || '') : ''
    const baseUrl = runtimeBase ? new URL(runtimeBase, window.location.href) : new URL('/', window.location.href)
    const wsProto = baseUrl.protocol === 'https:' ? 'wss:' : (baseUrl.protocol === 'http:' ? 'ws:' : (window.location.protocol === 'https:' ? 'wss:' : 'ws:'))
    const basePath = (baseUrl.pathname || '/').replace(/\/$/, '')
    const path = `${basePath}/api/v1/cases/messages/ws`
    const origin = `${wsProto}//${baseUrl.host}`
    const url = `${origin}${path}?uid=${encodeURIComponent(encUid)}&sid=${encodeURIComponent(sid)}`

    log.debug("ws url:", url)

    return url
  } catch (_) {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${wsProto}//${window.location.host}/api/v1/cases/messages/ws?uid=${encodeURIComponent(encUid)}&sid=${encodeURIComponent(sid)}`
  }
}

function scheduleReconnect() {
  if (!_shouldReconnect) return
  if (_reconnectTimer) return
  const delay = Math.min(30000, 1000 * Math.pow(2, _reconnectAttempts || 0))
  _reconnectTimer = setTimeout(() => {
    _reconnectTimer = null
    _reconnectAttempts = Math.min(_reconnectAttempts + 1, 5)
    _connect()
  }, delay)
}

async function _ensureIds() {
  if (_encUserId && _sessionId) return
  // Primary: ask backend for user info and session id; works with HttpOnly cookies
  try {
    const me = await api.get('/api/v1/auth/me').then(r => r?.data)
    if (me) {
      if (me.id) _encUserId = _encUserId || me.id
      if (me.session_id) _sessionId = _sessionId || me.session_id
    }
  } catch (_) {
    // ignore; fallback to header/token parsing below
  }
  if (_encUserId && _sessionId) return
  // Fallback: Extract session id (jti) from token found in axios Authorization header or non-HttpOnly cookie
  let token = ''
  try {
    const auth = api?.defaults?.headers?.common?.Authorization || api?.defaults?.headers?.common?.authorization
    if (typeof auth === 'string' && auth.length) token = auth
  } catch (_) { /* noop */ }
  if (!token) {
    token = getCookie('access_token') || ''
  }
  if (typeof token === 'string' && token.startsWith('Bearer ')) {
    token = token.slice(7)
  }
  const jti = parseJwtJti(token)
  if (jti) {
    _sessionId = _sessionId || jti
  }
}

function _connect() {

  log.debug("_connect start")

  if (_ws || _connecting) {
    log.info("_connect skipped: already connected or connecting")
    return
  }

  if (!_encUserId || !_sessionId) {
    log.warn("_connect blocked: missing encUserId or sessionId", { _encUserId: !!_encUserId, _sessionId: !!_sessionId })
    return
  }

  _connecting = true
  try {
    const url = getWsUrl(_encUserId, _sessionId)
    const ws = new WebSocket(url)
    _ws = ws

    ws.onopen = () => {
      _connecting = false
      _reconnectAttempts = 0

      log.debug("_connect success")

      // Initialize counts immediately on connect via API (in case no push yet)
      // Uses api wrapper per project guidelines
      try {
        api.get('/api/v1/cases/messages/unseen_messages_counts')
          .then(r => r && r.data)
          .then(data => {
            if (data && typeof data === 'object') {
              gMessageCounts.value = { ...data }
              log.debug('counts.init', data)
            }
          })
          .catch((err) => {
            try {
              const status = err && err.response && err.response.status
              if (status === 419) {
                // Session expired while initializing counts; unhook websocket per requirement
                disconnectMessagesWS({ clearCounts: true })
              }
            } catch (_) { /* noop */ }
          })
      } catch (_) { /* noop */ }
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data || '{}')
        if (data?.type === 'counts.update' && data?.counts && typeof data.counts === 'object') {
          // Replace counts object (keep it simple; consumers should watch ref value)
          gMessageCounts.value = { ...data.counts }

          log.debug("counts.update", data.counts)

        } else if (data?.type === "messages.change" || data?.type == "reactions.update") {
          log.debug(data?.type, data)
          try {
            const detail = {
              case_id: data?.case_id || null,
              message_id: data?.message_id || null,
            }
            if (detail.case_id && detail.message_id) {
              // New generalized event consumers should listen to 'message-change'
              gMessageEvents?.dispatchEvent?.(new CustomEvent('message-change', { detail }))
              // Backward compatibility: also dispatch legacy event on reactions.update
              if (data?.type == "reactions.update") {
                gMessageEvents?.dispatchEvent?.(new CustomEvent('message-reaction-update', { detail }))
              }
            }
          } catch (_) { /* noop */ }
        } else if (data?.type === 'pong') {
          // noop
        }
      } catch (e) {
        // ignore
      }
    }

    ws.onclose = () => {
      _ws = null
      _connecting = false
      if (_shouldReconnect) scheduleReconnect()
    }

    ws.onerror = () => {
      try { ws.close() } catch {}
    }
  } catch (e) {
    _connecting = false
    scheduleReconnect()
  }
}

export async function initMessagesWS() {

  log.debug("initMessagesWS start")

  if (_inited) {
    log.info("initMessagesWS: already initialized; skipping")
    return
  }
  _shouldReconnect = true

  await _ensureIds()

  log.debug("initMessagesWS ensureIds done", _encUserId, _sessionId)

  if (_encUserId && _sessionId) {
    _inited = true
    _connect()
  } else {

    log.debug("initMessagesWS bad user or session")

    if (!_initRetryTimer) {
      _initRetryTimer = setInterval(async () => {
        await _ensureIds()
        if (_encUserId && _sessionId) {
          try { clearInterval(_initRetryTimer) } catch {}
          _initRetryTimer = null
          _inited = true
          _connect()
        }
      }, 2000)
    }
  }
}

export function disconnectMessagesWS(options = {}) {
  const { clearCounts = true } = options
  _shouldReconnect = false
  _inited = false
  _connecting = false
  _reconnectAttempts = 0
  try { if (_initRetryTimer) clearInterval(_initRetryTimer) } catch {}
  _initRetryTimer = null
  try { if (_reconnectTimer) clearTimeout(_reconnectTimer) } catch {}
  _reconnectTimer = null
  try {
    if (_ws) { _ws.close() }
  } catch {}
  _ws = null
  _encUserId = null
  _sessionId = null
  if (clearCounts) {
    gMessageCounts.value = {}
  }
}

// App-start bootstrap: if a valid session id exists, initialize WS once.
export async function maybeInitMessagesWSOnLoad() {
  try {
    if (_inited || _ws) return

    // Do not probe auth/me on public routes (e.g., login) to avoid 419 + toast on first arrival
    try {
      const current = router?.currentRoute?.value
      const isPublic = !!(current?.meta && current.meta.public)
      const isLogin = current?.name === 'login'
      if (isPublic || isLogin) return
    } catch (_) { /* noop */ }

    // Fast check via /api/v1/auth/me (works with HttpOnly cookie or Authorization header)
    let me = null
    try {
      me = await api.get('/api/v1/auth/me').then(r => r?.data)
    } catch (_) { /* ignore */ }

    if (me && me.session_id) {
      // We have a valid session from backend; seed ids and init
      _sessionId = _sessionId || me.session_id
      if (me.id) _encUserId = _encUserId || me.id
      await initMessagesWS()
      return
    }

    // Fallback: try to detect jti from Authorization header or non-HttpOnly cookie
    let token = ''
    try {
      const auth = api?.defaults?.headers?.common?.Authorization || api?.defaults?.headers?.common?.authorization
      if (typeof auth === 'string' && auth.length) token = auth
    } catch (_) { /* noop */ }
    if (!token) {
      token = getCookie('access_token') || ''
    }
    if (typeof token === 'string' && token.startsWith('Bearer ')) {
      token = token.slice(7)
    }
    const jti = parseJwtJti(token)
    if (jti) {
      _sessionId = _sessionId || jti
      // Let initMessagesWS run its normal ensure/connect flow
      await initMessagesWS()
    }
    // If no jti and /me failed, do nothing (no timers, per requirement)
  } catch (_) {
    // swallow errors on bootstrap
  }
}
