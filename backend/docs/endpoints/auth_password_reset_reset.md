Endpoint: POST /api/v1/auth/password-reset/reset

Purpose
- Complete the password reset by setting a new password using a previously emailed reset token.

Request
- URL: /api/v1/auth/password-reset/reset
- Method: POST
- Content-Type: application/json
- Authentication: not required
- Body schema (PasswordResetConfirm):
  {
    "token": "string (UUID hex, stored in app_user_session.jti)",
    "new_password": "string"
  }
- Example:
  {
    "token": "3f2a1b4c5d6e7f8091a2b3c4d5e6f708",
    "new_password": "NewSecurePassword123"
  }
- cURL example:
  curl -X POST "http://localhost:8000/api/v1/auth/password-reset/reset" \
       -H "Content-Type: application/json" \
       -d '{"token": "3f2a1b4c5d6e7f8091a2b3c4d5e6f708", "new_password": "NewSecurePassword123"}'

Responses
- 200 OK
  {
    "message": "Password has been reset"
  }

- 400 Bad Request (invalid or expired token)
  {
    "detail": "Invalid or expired token"
  }

Behavior
- Validates that the provided token exists in the app_user_session table, is active, and not expired.
- If valid, retrieves the associated user, updates the user's password hash, commits the change, and invalidates the token (so it cannot be reused).
- If the token is invalid/expired or the session is not found, responds with 400.

Notes
- Tokens for password reset are created by the password reset request endpoint and stored as app_user_session rows with a short expiration (default 60 minutes).
- No authentication is required to perform this action, but possession of a valid token is necessary.
- Password hashing uses the configured scheme in app/core/security.py.

Related Models
- PasswordResetConfirm (app/schemas/auth.py)
- AppUserSession (app/db/models/app_user_session.py)
- AppUser (app/db/models/app_user.py)

Implementation
- Handler: app/api/v1/endpoints/auth.py::reset_password
- Session validation/invalidation: app/services/auth.py::validate_session, ::invalidate_session
- Password hashing: app/core/security.py::get_password_hash

Related endpoints
- POST /api/v1/auth/password-reset/request (initiates reset and emails token)

Global error handling
- 500 Internal Server Error (unhandled exceptions) returns a JSON response with trace and X-Error-ID header, as configured in main.py.
