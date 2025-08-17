Endpoint: GET /api/v1/auth/me

Purpose
- Retrieve information about the currently authenticated user.

Request
- URL: /api/v1/auth/me
- Method: GET
- Headers:
  - Authorization: Bearer <access_token>

Responses
- 200 OK (UserInfo)
  {
    "id": 123,
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "is_active": true
  }

- 401 Unauthorized (invalid/expired token or invalidated session)
  {
    "detail": "Could not validate credentials"
  }

- 403 Not authenticated (missing Authorization header)
  - Raised by HTTPBearer when the header is not present.

Notes
- Requires a valid, non-expired JWT whose session (jti) is still active on the server.
- After calling /api/v1/auth/logout, the same token cannot access /me and will yield 401.

Related Models
- UserInfo (app/schemas/auth.py)

Implementation
- Handler: app/api/v1/endpoints/auth.py::get_current_user_info
- Dependency: app/api/dependencies.py::get_current_user (validates JWT and session)

Related tests
- tests/test_auth.py (happy path, invalid token, expired token, logout invalidation)

Test intent and coverage
- Verify happy path: valid token returns 200 with UserInfo matching the logged-in user.
- Verify invalid credentials: malformed/invalidated/expired token returns 401 with detail "Could not validate credentials".
- Verify missing Authorization header: FastAPI responds 403 Not authenticated.
- Regression guard: ensures response shape and security enforcement remain stable.

Global error handling
- 500 Internal Server Error:
  - Returned for unhandled exceptions. Response body:
    {
      "detail": "Internal Server Error",
      "error": "<string message>",
      "error_type": "<ExceptionClass>",
      "trace": "<stack trace string>",
      "error_id": "<UUID>",
      "path": "/api/v1/auth/me",
      "method": "GET"
    }
  - Headers:
    - X-Error-ID: <same UUID as error_id> (use this when reporting issues)
