Endpoint: POST /api/v1/auth/login

Purpose
- Authenticate a user and return a JWT access token for use with the Authorization: Bearer header.

Request
- URL: /api/v1/auth/login
- Method: POST
- Content-Type: application/json
- Authentication: not required
- Body schema (LoginRequest):
  {
    "email": "string (email)",
    "password": "string"
  }
- Example (minimal):
  {
    "email": "user@example.com",
    "password": "YourSecurePassword123"
  }
- cURL example:
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
       -H "Content-Type: application/json" \
       -d '{"email": "user@example.com", "password": "YourSecurePassword123"}'

Responses
- 200 OK (TokenResponse)
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }

- 401 Unauthorized (incorrect credentials)
  {
    "detail": "Incorrect email or password"
  }

- 401 Unauthorized (inactive account)
  {
    "detail": "Account is inactive"
  }

Usage
- Include the token in the Authorization header for subsequent requests:
  Authorization: Bearer <access_token>

Notes
- Tokens expire after settings.access_token_expire_minutes.
- On each login, a server-side session is created; logging out invalidates the session.
- Occasionally (≈1% of logins) the server performs cleanup of expired sessions.

Related Models
- LoginRequest (app/schemas/auth.py)
- TokenResponse (app/schemas/auth.py)

Implementation
- Handler: app/api/v1/endpoints/auth.py::login
- Authentication check: app/services/auth.py::authenticate_user
- Token creation: app/core/security.py::create_access_token
- Sessions: app/services/auth.py::create_user_session / invalidate_session

Related tests
- tests/test_auth.py

Test intent and coverage
- Verify happy path: valid credentials return 200 and a JWT with token_type "bearer"; token authorizes /api/v1/auth/me.
- Verify invalid credentials: non-existent user or wrong password returns 401 with "Incorrect email or password".
- Verify inactive account: inactive users cannot log in and receive 401 with "Account is inactive".
- Verify logout invalidation: after /api/v1/auth/logout, the same token cannot access /me (401, "Could not validate credentials").
- Verify token expiry: with a very short expiry, token works immediately and then expires, causing 401 on subsequent protected calls.
- Regression guard: ensures status codes, response shapes, and security flows remain stable across changes.

Global error handling
- 500 Internal Server Error:
  - Returned for unhandled exceptions. Response body:
    {
      "detail": "Internal Server Error",
      "error": "<string message>",
      "error_type": "<ExceptionClass>",
      "trace": "<stack trace string>",
      "error_id": "<UUID>",
      "path": "/api/v1/auth/login",
      "method": "POST"
    }
  - Headers:
    - X-Error-ID: <same UUID as error_id> (use this when reporting issues)
