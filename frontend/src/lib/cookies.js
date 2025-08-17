// Tiny cookie helper with secure defaults
// Note: HttpOnly cannot be set from JavaScript. For true protection against XSS,
// set HttpOnly cookies from the server. This utility uses Secure and SameSite flags
// to improve security compared to localStorage.

export function setCookie(name, value, options = {}) {
  const {
    // maxAge in seconds; if not provided, it becomes a session cookie
    maxAge,
    // expires: Date instance; will be ignored if maxAge is provided
    expires,
    path = '/',
    sameSite = 'Strict', // 'Lax' | 'Strict' | 'None'
    secure = true,
    domain,
  } = options

  let cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}`

  if (typeof maxAge === 'number') {
    cookie += `; Max-Age=${Math.floor(maxAge)}`
  } else if (expires instanceof Date) {
    cookie += `; Expires=${expires.toUTCString()}`
  }

  if (path) cookie += `; Path=${path}`
  if (domain) cookie += `; Domain=${domain}`
  if (sameSite) cookie += `; SameSite=${sameSite}`
  if (secure) cookie += `; Secure`

  document.cookie = cookie
}

export function getCookie(name) {
  const cookies = document.cookie ? document.cookie.split('; ') : []
  for (const c of cookies) {
    const [k, v] = c.split('=')
    if (decodeURIComponent(k) === name) {
      return decodeURIComponent(v || '')
    }
  }
  return null
}

export function deleteCookie(name, options = {}) {
  // Delete by setting Max-Age=0 and an expired date; must include same Path/Domain used to set it
  const { path = '/', domain } = options
  const base = `${encodeURIComponent(name)}=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=${path}`
  const domainPart = domain ? `; Domain=${domain}` : ''
  // Attempt delete without Secure
  document.cookie = `${base}${domainPart}; SameSite=Strict`
  // Attempt delete with Secure (covers cookies created with Secure flag)
  document.cookie = `${base}${domainPart}; SameSite=Strict; Secure`
}
