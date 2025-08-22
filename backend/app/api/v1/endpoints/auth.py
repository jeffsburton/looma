from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic.v1 import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import uuid

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo, PasswordResetRequest, PasswordResetConfirm, MessageResponse
from app.schemas.user import UserRead, UserCreate
from app.services.auth import authenticate_user, create_user_session, invalidate_session, cleanup_expired_sessions, extend_session, validate_session, get_user_permission_codes
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from app.api.dependencies import get_current_user, security, get_bearer_or_cookie_token, validate_csrf
from app.db.models.app_user import AppUser
from app.services.telegram import send_telegram_dm
from app.services.user import create_user, get_user_by_email, get_user_by_id
from app.services.email import send_email
import logging

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """User registration endpoint"""
    # Check if user already exists
    existing_user = await get_user_by_email(db, str(user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user = await create_user(db, user_data)

    # Notify admin about new registration (non-blocking in terms of success; log failures)
    try:
        admin_email = getattr(settings, "admin_notification_email", None)
        if admin_email:
            subject = f"[{settings.project_name}] New user registration"
            full_name = f"{user.first_name} {user.last_name}".strip()
            text = (
                "A new user has registered on the system.\n\n"
                f"Name: {full_name}\n"
                f"Email: {user.email}\n"
                f"Phone: {user.phone}\n"
                f"Telegram: {user.telegram}\n"
            )
            send_email(to=admin_email, subject=subject, text=text)
            if user.telegram:
                send_telegram_dm(to=user.telegram, text=text)
    except Exception as e:
        logging.getLogger(__name__).warning(
            "Failed to send admin registration notification: %s", e
        )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access token",
    description=(
        "Authenticate a user with email and password.\n\n"
        "Request body: LoginRequest { email: string (email), password: string }.\n\n"
        "On success returns TokenResponse with a JWT access_token and token_type=\"bearer\".\n\n"
        "Use the token in the Authorization header for subsequent requests: \n"
        "Authorization: Bearer <access_token>.\n\n"
        "Possible errors: 401 Incorrect email or password; 401 Account is inactive."
    ),
    response_description="Bearer token to authorize subsequent API calls",
    responses={
        200: {
            "description": "Successful login",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "codes": ["users.read", "users.write"]
                    }
                }
            }
        },
        401: {
            "description": "Unauthorized: incorrect credentials or inactive account",
            "content": {
                "application/json": {
                    "examples": {
                        "bad_credentials": {
                            "summary": "Incorrect email or password",
                            "value": {"detail": "Incorrect email or password"}
                        },
                        "inactive": {
                            "summary": "Account is inactive",
                            "value": {"detail": "Account is inactive"}
                        }
                    }
                }
            }
        }
    }
)
async def login(
        login_data: LoginRequest,
        db: AsyncSession = Depends(get_db),
        response: Response = None
):
    """User login endpoint. Returns a JWT for use in the Authorization header and sets an auth cookie.
    If CSRF is enabled, also sets a CSRF cookie for Double-Submit Cookie protection.
    """
    user = await authenticate_user(db, str(login_data.email), login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Check if user account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )

    # Occasionally cleanup old sessions (every ~1% of logins)
    import random
    if random.randint(1, 100) == 1:
        await cleanup_expired_sessions(db, older_than_days=7)


    # Create session
    jti = str(uuid.uuid4())
    await create_user_session(
        db,
        user.id,
        jti,
        settings.access_token_expire_minutes
    )

    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        sub=user.email,
        jti=jti,
        expires_delta=access_token_expires
    )

    # Set cookie for browser clients (keep JSON response for API clients)
    max_age = settings.access_token_expire_minutes * 60
    if response is not None:
        response.set_cookie(
            key=settings.cookie_name,
            value=access_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=max_age,
            expires=max_age,
            path=settings.cookie_path,
            domain=settings.cookie_domain
        )
        # If CSRF DSC is enabled, set a readable CSRF cookie too
        if settings.csrf_protection_enabled:
            import uuid as _uuid
            csrf_val = _uuid.uuid4().hex
            response.set_cookie(
                key=settings.csrf_cookie_name,
                value=csrf_val,
                httponly=False,
                secure=settings.cookie_secure,
                samesite=settings.cookie_samesite,
                max_age=max_age,
                expires=max_age,
                path=settings.cookie_path,
                domain=settings.cookie_domain
            )

    # Gather user permission codes
    codes = await get_user_permission_codes(db, user.id)

    return TokenResponse(access_token=access_token, codes=codes)

@router.post("/logout")
async def logout(
        token: str = Depends(get_bearer_or_cookie_token),
        db: AsyncSession = Depends(get_db),
        response: Response = None,
        _csrf: None = Depends(validate_csrf)
):
    """User logout endpoint"""
    try:
        from jose import jwt
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        jti = payload.get("jti")

        if jti:
            await invalidate_session(db, jti)

    except Exception:
        # Ignore errors; we'll still return success and clear cookie below
        pass

    # Clear cookie on client if Response provided
    if response is not None:
        response.delete_cookie(
            key=settings.cookie_name,
            path=settings.cookie_path,
            domain=settings.cookie_domain,
            samesite=settings.cookie_samesite
        )
        if settings.csrf_protection_enabled:
            response.delete_cookie(
                key=settings.csrf_cookie_name,
                path=settings.cookie_path,
                domain=settings.cookie_domain,
                samesite=settings.cookie_samesite
            )

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
        token: str = Depends(get_bearer_or_cookie_token),
        db: AsyncSession = Depends(get_db),
        response: Response = None,
        _csrf: None = Depends(validate_csrf)
):
    """Refresh the access token and extend the session expiry (rolling session).
    Requires a valid session. Re-sets the auth cookie and returns the token.
    """
    from jose import jwt
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm]
    )
    email: str = payload.get("sub")
    jti: str = payload.get("jti")

    if not email or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    session = await extend_session(db, jti, settings.access_token_expire_minutes)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expired")

    # Issue new JWT (same jti, new exp)
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        sub=email,
        jti=jti,
        expires_delta=access_token_expires
    )

    max_age = settings.access_token_expire_minutes * 60
    if response is not None:
        response.set_cookie(
            key=settings.cookie_name,
            value=access_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=max_age,
            expires=max_age,
            path=settings.cookie_path,
            domain=settings.cookie_domain
        )

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
        current_user: AppUser = Depends(get_current_user)
):
    """Get current user information"""
    return UserInfo(
        id=current_user.id,
        email=EmailStr(current_user.email),
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active
    )


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
        payload: PasswordResetRequest,
        db: AsyncSession = Depends(get_db)
):
    """Request a password reset link to be emailed to the user.
    - Verifies the email exists (404 if not).
    - Creates a short-lived token stored in app_user_session.
    - Sends an email containing a link with the token.
    - Returns success on completion.
    """
    email = str(payload.email)
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    # Create a reset token using the existing session table
    token = uuid.uuid4().hex
    await create_user_session(
        db,
        user_id=user.id,
        jti=token,
        expires_minutes=getattr(settings, "password_reset_token_expire_minutes", 60),
    )

    # Build absolute link using configured frontend base URL
    base_url = settings.effective_frontend_base_url.rstrip("/")
    reset_path = "/reset-password?token=" + token
    reset_url = f"{base_url}{reset_path}"

    subject = f"{settings.project_name} - Password Reset Request"
    text = (
        f"Hello {user.first_name},\n\n"
        f"We received a request to reset your password.\n"
        f"Use the following link to reset your password (it expires in "
        f"{getattr(settings, 'password_reset_token_expire_minutes', 60)} minutes):\n\n"
        f"{reset_url}\n\n"
        f"If you did not request a password reset, please ignore this email."
    )

    # HTML version with a dark red button
    html = (
        f"""
        <div style=\"font-family: Arial, sans-serif; line-height:1.6; color:#222;\">
          <p>Hello {user.first_name},</p>
          <p>We received a request to reset your password. Click the button below to proceed. This link expires in {getattr(settings, 'password_reset_token_expire_minutes', 60)} minutes.</p>
          <p style=\"margin: 24px 0;\">
            <a href=\"{reset_url}\" target=\"_blank\" style=\"background-color:#8B0000; color:#ffffff; padding:12px 20px; border-radius:6px; text-decoration:none; display:inline-block; font-weight:600;\">Reset Password</a>
          </p>
          <p>If the button doesn't work, copy and paste this URL into your browser:</p>
          <p><a href=\"{reset_url}\">{reset_url}</a></p>
          <p>If you did not request a password reset, please ignore this email.</p>
        </div>
        """
    )

    # Send email via configured backend (memory/console/smtp)
    send_email(to=email, subject=subject, text=text, html=html)

    return {"message": "Password reset email sent"}


@router.post(
    "/password-reset/reset",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
    summary="Reset password using a valid token",
    description=(
        "Complete the password reset by providing the token received in email and the new password.\n\n"
        "The token must exist in app_user_session, be active, and not expired."
    ),
    responses={
        200: {
            "description": "Password successfully reset",
            "content": {"application/json": {"example": {"message": "Password has been reset"}}},
        },
        400: {
            "description": "Invalid or expired token",
            "content": {"application/json": {"example": {"detail": "Invalid or expired token"}}},
        },
    },
)
async def reset_password(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Reset the user's password given a valid reset token."""
    token = payload.token
    new_password = payload.new_password

    # Validate session token
    session = await validate_session(db, token)
    if not session:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    # Get the user associated with the session
    user = await get_user_by_id(db, session.app_user_id)
    if not user:
        # Shouldn't happen if FK integrity holds, but handle gracefully
        # Also invalidate the token if orphaned
        await invalidate_session(db, token)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    # Update user's password
    user.password_hash = get_password_hash(new_password)
    db.add(user)
    await db.commit()

    # Invalidate the reset token so it can't be reused
    await invalidate_session(db, token)

    return MessageResponse(message="Password has been reset")