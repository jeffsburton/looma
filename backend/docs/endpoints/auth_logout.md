Endpoint: POST /api/v1/auth/logout

Purpose
- Invalidate the current session so the presented access token can no longer be used.

Request
- URL: /api/v1/auth/logout
- Method: POST
- Headers:
  - Authorization: Bearer <access_token>

Responses
- 200 OK
  {
    "message": "Successfully logged out"
  }

Notes
- Idempotent: The endpoint always returns a 200 with the same message, even if the token is invalid/expired or lacks a valid session reference.
- When a valid JWT is supplied, the server reads its jti (token ID) and invalidates the corresponding server-side session. Subsequent use of that token for protected endpoints (e.g., /api/v1/auth/me) will fail with 401.
- If the Authorization header is missing, FastAPI’s HTTPBearer(auto_error=True) will reject the request before it reaches the handler (typically 403 Not authenticated).

Related Models
- None (the request uses only the Authorization header; the response is a simple message object).

Implementation
- Handler: app/api/v1/endpoints/auth.py::logout
- Auth dependency: app/api/dependencies.py::security (HTTPBearer)
- Session invalidation: app/services/auth.py::invalidate_session

Related tests
- tests/test_auth.py (logout invalidation behavior)

Test intent and coverage
- Verify happy path: returns 200 with a success message.
- Verify invalid/expired token: still returns 200, but subsequent use of the token at /me fails with 401.
- Verify idempotency: repeated calls with same or invalid token behave consistently.
- Verify missing Authorization header: FastAPI rejects with 403 (Not authenticated).
- Regression guard: ensures logout semantics and messaging remain stable.

Global error handling
- 500 Internal Server Error:
  - Returned for unhandled exceptions. Response body:
    {
      "detail": "Internal Server Error",
      "error": "<string message>",
      "error_type": "<ExceptionClass>",
      "trace": "<stack trace string>",
      "error_id": "<UUID>",
      "path": "/api/v1/auth/logout",
      "method": "POST"
    }
  - Headers:
    - X-Error-ID: <same UUID as error_id> (use this when reporting issues)
