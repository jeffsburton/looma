Endpoint: POST /api/v1/auth/password-reset/request

Purpose
- Initiate a password reset flow by emailing the user a time-limited reset link containing a token.

Request
- URL: /api/v1/auth/password-reset/request
- Method: POST
- Content-Type: application/json
- Authentication: not required
- Body schema (PasswordResetRequest):
  {
    "email": "string (email)"
  }
- Example:
  {
    "email": "user@example.com"
  }
- cURL example:
  curl -X POST "http://localhost:8000/api/v1/auth/password-reset/request" \
       -H "Content-Type: application/json" \
       -d '{"email": "user@example.com"}'

Responses
- 200 OK
  {
    "message": "Password reset email sent"
  }

- 404 Not Found (unknown email)
  {
    "detail": "Email not found"
  }

Behavior
- Verifies that a user with the provided email exists; if not, returns 404 and does not send an email.
- Generates a secure, random token (UUID hex) and stores it in the app_user_session table as a short-lived, active session record.
- Sends an email to the user with an absolute reset link in the form:
  {frontend_base_url}/reset-password?token=<token>
  where {frontend_base_url} depends on environment:
  - development: http://localhost:5173
  - training: https://looma-training.c2r.one
  - production: https://looma-c2r.one
- The token expires after settings.password_reset_token_expire_minutes (default: 60 minutes).

Notes
- The link domain is configurable via settings.frontend_env and the corresponding base URLs. See app/core/config.py: effective_frontend_base_url.
- Email delivery backend is configured via settings.email_backend (smtp | console | memory):
  - smtp: sends via configured SMTP server.
  - console: prints the email to stdout (useful for dev).
  - memory: stores the message in an in-memory outbox (used in tests).
- The session entry created for the token uses the AppUserSession model and is marked active until it expires or is invalidated.
- This endpoint sends the reset email. The actual password update is handled by POST /api/v1/auth/password-reset/reset using the provided token.

Related Models
- PasswordResetRequest (app/schemas/auth.py)
- AppUserSession (app/db/models/app_user_session.py)

Implementation
- Handler: app/api/v1/endpoints/auth.py::request_password_reset
- Session creation: app/services/auth.py::create_user_session
- User lookup: app/services/user.py::get_user_by_email
- Email sending: app/services/email.py::send_email
- Settings: app/core/config.py (password_reset_token_expire_minutes, email backend/SMTP settings)

Related tests
- tests/test_password_reset.py

Test intent and coverage
- Successful request: returns 200, sends an email containing /password-reset?token=<token>, and persists the token in app_user_session for the user.
- Non-existent email: returns 404 and does not send an email.

Global error handling
- 500 Internal Server Error (unhandled exceptions) returns a JSON response with trace and X-Error-ID header, as configured in main.py.
