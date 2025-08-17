Endpoint: POST /api/v1/auth/register

Purpose
- Create a new user account.

Request
- URL: /api/v1/auth/register
- Method: POST
- Content-Type: application/json
- Body schema (UserCreate):
  {
    "first_name": "string",
    "last_name": "string",
    "email": "string (email)",
    "password": "string",
    "phone": "string | null (optional)",
    "organization": "string | null (optional)",
    "referred_by": "string | null (optional)"
  }
- Example (minimal):
  {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "password": "securepassword123"
  }
- Example (with optionals):
  {
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@example.com",
    "password": "securepassword123",
    "phone": "+1234567890",
    "organization": "Test Company",
    "referred_by": "John Doe"
  }

Responses
- 201 Created (UserRead)
  {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "is_active": true,
    "phone": null,
    "organization": null,
    "referred_by": null,
    "created_at": "2025-08-15T06:00:00Z",
    "updated_at": "2025-08-15T06:00:00Z"
  }

- 400 Bad Request (duplicate email)
  {
    "detail": "Email already registered"
  }

- 422 Unprocessable Entity (validation errors)
  - Returned by FastAPI/Pydantic for invalid/missing fields (e.g., invalid email, missing last_name/password).

Notes
- Authentication is not required for registration.
- The password is accepted in the request but is never returned in responses. Password hashes are not exposed.
- Newly created users are active by default unless business rules change.

Related Models
- UserCreate (app/schemas/user.py)
- UserRead (app/schemas/user.py)

Implementation
- Handler: app/api/v1/endpoints/auth.py::register
- Create user: app/services/user.py::create_user
- Duplicate check: app/services/user.py::get_user_by_email

Related tests
- tests/test_register.py
- tests/test_auth.py (flow: register then login)

Test intent and coverage
- Verify happy path: valid payload returns 201 with a UserRead object (no password fields).
- Verify optional fields: phone, organization, referred_by are persisted and returned.
- Verify duplicate email: returns 400 with detail "Email already registered".
- Verify validation errors: invalid email or missing required fields return 422.
- Regression guard: ensures response shape, status codes, and validation behavior remain stable.

Global error handling
- 500 Internal Server Error:
  - Returned for unhandled exceptions. Response body:
    {
      "detail": "Internal Server Error",
      "error": "<string message>",
      "error_type": "<ExceptionClass>",
      "trace": "<stack trace string>",
      "error_id": "<UUID>",
      "path": "/api/v1/auth/register",
      "method": "POST"
    }
  - Headers:
    - X-Error-ID: <same UUID as error_id> (use this when reporting issues)
