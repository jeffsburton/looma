# Backend refactor: switching to HttpOnly session cookies

This document lists the information needed to safely refactor the backend to server-managed HttpOnly session cookies and interop details with the existing frontend.

## What information do we need to proceed?

1. Cookie contract
   - Cookie name (e.g., `session`, `access_token`)
   - Cookie scope
     - domain (e.g., `.example.com`, `localhost` for dev)
     - path (usually `/`)
   - Attributes
     - SameSite policy: `Strict`, `Lax`, or `None` (must be `None` if cross-site; requires `Secure`)
     - Secure: true in production (required if SameSite=None)
     - HttpOnly: true (prevents JS access)
   - Lifetime and rotation
     - TTL / Max-Age
     - Rolling session (refresh cookie on activity?)
     - Absolute session timeout
     - Clock skew tolerances
   - Payload style
     - Opaque random ID mapping to server/session store
     - Or stateless signed token (JWT) still in cookie
   - Multi-cookie strategy (optional)
     - Separate refresh token cookie? Name/attrs

2. Authentication flow
   - Login endpoint
     - Path (e.g., `POST /api/auth/login`)
     - Request payload shape (username/password or OAuth)
     - Response: Set-Cookie header(s) format
   - Logout endpoint
     - Path (e.g., `POST /api/auth/logout`)
     - Should clear cookie via `Set-Cookie` with `Max-Age=0` and the same Path/Domain attributes used to set
   - Session refresh/extend endpoint (if using refresh tokens or rolling sessions)
     - Path and behavior

3. CSRF protection strategy
   - Chosen approach
     - SameSite=Lax with cookie-only sessions and safe navigation requirements
     - OR Double-Submit Cookie (DSC) token: names for the CSRF cookie and header (e.g., `X-CSRF-Token`)
     - OR Synchronizer Token via session-backed CSRF token endpoint
   - For DSC, specify:
     - CSRF cookie name and attributes
     - Header name the frontend must send (e.g., `X-CSRF-Token`)
     - Whether to read CSRF token from a cookie or a bootstrap endpoint

4. CORS and dev proxy
   - Allowed origins (dev and prod)
   - Whether credentials are allowed (must be true for cookies)
   - Headers exposed/allowed (e.g., `X-Error-ID`, CSRF header)
   - Vite dev server proxy path and target (frontend uses baseURL `/` and relies on proxying `/api` to backend)

5. Error response schema (for consistency with UI error dialog)
   - Standardized fields: `detail`, `error`, `error_type`, `trace` (dev only), `error_id`
   - HTTP headers conveying error id (e.g., `X-Error-ID`)

6. Environment-specific values
   - Dev vs prod cookie attributes (Secure/SameSite, domain)
   - HTTPS availability in dev
   - Reverse proxy settings (path prefixes, domain)

7. Session storage/backing
   - If using server-side session store: storage type (memory, Redis, DB), capacity, eviction policy
   - If using JWT-in-cookie: signing keys/rotation, audience/issuer, token size constraints

## Frontend interop notes

- Axios is configured to send credentials (cookies) by default.
  - See `src/lib/api.js` with `withCredentials: true`.
- If the session cookie is HttpOnly, the frontend cannot delete it; logout must call the backend logout endpoint which clears the cookie.
  - Current UI calls `deleteCookie('access_token')` in `HomeView.vue`. Keep this for now for backward compatibility; plan to switch to calling the backend logout endpoint as soon as it’s available.
- If CSRF uses the Double-Submit Cookie pattern, confirm:
  - CSRF cookie name and header name, so the frontend can read the cookie value and send the header for state-changing requests.

## Action items once the info is provided

- Backend
  - Implement login/logout/refresh with proper Set-Cookie/Clear-Cookie semantics and CSRF strategy.
  - Configure CORS to allow credentials from the frontend origin(s).
- Frontend
  - Remove Authorization header injection once cookie-only auth is active.
  - Replace `deleteCookie('access_token')` with a call to the backend logout endpoint.
  - If applicable, add CSRF header injection for unsafe methods using the CSRF cookie value.


## Security implications of the interim frontend auth flag

This project currently uses a minimal client-side fallback to address routing after login:
- On successful login, the frontend sets localStorage key `is_authenticated = '1'`.
- The router guard allows navigation to protected routes if either:
  - A readable `access_token` cookie exists, or
  - The `is_authenticated` flag is present.

This is a temporary workaround to bridge two worlds: token-in-browser vs. server-managed HttpOnly session cookies. It helps avoid a redirect loop when the backend sets an HttpOnly cookie (which JavaScript cannot read), but it has important security considerations.

What this flag is and isn’t
- It is only a client-side routing hint. It does not grant API access. All protected data must still be enforced on the server by requiring the session cookie (or Authorization header if applicable).
- It is not a security boundary. An attacker with the ability to run JavaScript in the browser (e.g., via XSS) can set or remove this flag at will.

Key risks and how to mitigate them
1) XSS (Cross-Site Scripting)
   - Risk: If an attacker can execute JS on your site (XSS), they can set `localStorage.is_authenticated = '1'` and access client-side screens.
   - Impact: Primarily UI exposure. Sensitive data should still be fetched from APIs that require an authenticated session (cookie). If any page embeds sensitive information without an API/auth check, that data could be exposed.
   - Mitigations:
     - Avoid dangerous HTML injection (no untrusted v-html; sanitize user content).
     - Use a Content Security Policy (CSP) that disallows inline scripts and restricts sources.
     - Keep dependencies up to date; use Vue’s default escaping for bindings.

2) CSRF (Cross-Site Request Forgery) with cookie-based sessions
   - Risk: When auth is cookie-based, browsers automatically send cookies — making CSRF a concern for state-changing requests.
   - Mitigations (choose one strategy):
     - SameSite=Lax on the session cookie and ensure unsafe requests are XHR/fetch with custom headers (typical modern approach),
     - Or Double-Submit Cookie (DSC): issue a CSRF cookie and require the frontend to echo it in a header (e.g., X-CSRF-Token),
     - Or Synchronizer Token: backend-provided CSRF token linked to the session.
   - Action: Decide and document the CSRF strategy. If DSC is used, configure Axios to inject the CSRF header from the cookie for unsafe methods (POST/PUT/PATCH/DELETE).

3) UI/route exposure vs. actual data access
   - Risk: The router may allow navigation based on `is_authenticated` even when the server session expired. The UI might show shells of pages until API calls fail with 401.
   - Mitigations:
     - Ensure no sensitive data is rendered without API calls gated by server-side auth.
     - On 401 responses, clear the `is_authenticated` flag and redirect to login (planned enhancement to the Axios interceptor).

4) Logout consistency with HttpOnly cookies
   - Risk: The frontend cannot delete an HttpOnly cookie; a local deletion attempt won’t log the user out server-side.
   - Mitigations:
     - Provide a backend logout endpoint that clears the cookie using Set-Cookie with Max-Age=0 and matching Path/Domain.
     - Frontend should call that endpoint on logout, then clear local UI state and navigate to /login.

5) Session fixation and rotation
   - Risk: If using server-side sessions, failing to regenerate session ID on login can enable fixation attacks.
   - Mitigations:
     - Regenerate the session identifier on successful authentication.
     - Use rolling sessions and enforce absolute timeouts when appropriate.

6) Storage lifetime and “Remember me”
   - Consider the trade-offs of long-lived cookies vs. short sessions. For the temporary flag, storing `is_authenticated` only mirrors UI state; it should be cleared on logout and 401s.

Recommended production approach (target state)
- Use server-managed HttpOnly session cookies as the source of truth.
- Remove the Authorization header injection once fully cookie-only.
- Replace client-side `is_authenticated` routing hint with one of:
  - A short bootstrap call on app start (e.g., GET /api/auth/me) to set in-memory state; or
  - Rely solely on backend-protected API data, and optimistically show skeletons until data loads.
- Implement a clear CSRF strategy (SameSite and/or DSC) and wire up the frontend header injection if DSC is chosen.
- Implement backend logout and have the frontend call it; then clear local UI state and navigate to /login.
- Add an Axios 401 handler to clear UI auth state and optionally redirect to login.

Threat model summary
- The temporary `is_authenticated` flag does not weaken server-side protections as long as the backend enforces authentication for all sensitive data/actions.
- The main risks are:
  - XSS allowing UI navigation (but not bypassing server-side auth),
  - CSRF unless addressed by cookie attributes and/or CSRF tokens,
  - Inconsistent UI state if the server session expires.

Action items
- Backend:
  - Finalize cookie attributes (HttpOnly, Secure, SameSite), session rotation, logout endpoint, and CSRF strategy.
  - Configure CORS to allow credentials from the correct origins and expose required headers.
- Frontend:
  - Add 401 interceptor behavior to clear `is_authenticated` and route to login once backend semantics are finalized.
  - Remove the Authorization header injection and the local cookie token path when fully migrated to cookie-only sessions.
  - If DSC is chosen, add CSRF header injection to Axios for unsafe methods.
