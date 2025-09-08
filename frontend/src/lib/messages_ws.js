import { ref } from 'vue'
import api from '@/lib/api'
import { getCookie } from '@/lib/cookies'

// Global reactive map of counts keyed as specified, e.g.,
// count, count_rfis, count_<enc_case_id>, count_rfis_<enc_case_id>, ...
export const gMessageCounts = ref({})

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

    console.log("ws url:", url)

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

  console.log("_connect start")

  if (_ws || _connecting) return

  console.log("_connect already connecting")

  if (!_encUserId || !_sessionId) return

  console.log("_connect bad user or session")

  _connecting = true
  try {
    const url = getWsUrl(_encUserId, _sessionId)
    const ws = new WebSocket(url)
    _ws = ws

    ws.onopen = () => {
      _connecting = false
      _reconnectAttempts = 0

      console.log("_connect success")

      // Initialize counts immediately on connect via API (in case no push yet)
      // Uses api wrapper per project guidelines
      try {
        api.get('/api/v1/cases/messages/unseen_messages_counts')
          .then(r => r && r.data)
          .then(data => {
            if (data && typeof data === 'object') {
              gMessageCounts.value = { ...data }
              console.log('counts.init', data)
            }
          })
          .catch(() => {})
      } catch (_) { /* noop */ }
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data || '{}')
        if (data?.type === 'counts.update' && data?.counts && typeof data.counts === 'object') {
          // Replace counts object (keep it simple; consumers should watch ref value)
          gMessageCounts.value = { ...data.counts }

          console.log("counts.update", data.counts)

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

  console.log("initMessagesWS start")

  if (_inited) return
  _shouldReconnect = true

  console.log("initMessagesWS already inited")

  await _ensureIds()

  console.log("initMessagesWS ensureIds done", _encUserId, _sessionId)

  if (_encUserId && _sessionId) {
    _inited = true
    _connect()
  } else {

    console.log("initMessagesWS bad user or session")

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
