from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.config import settings
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.services.auth import validate_session, user_has_permission
from app.core.id_codec import decode_id, OpaqueIdError
from fastapi import Path
from typing import Callable

# Keep HTTPBearer for backward compatibility, but don't auto-error so we can fall back to cookie
security = HTTPBearer(auto_error=False)


def _is_state_changing(method: str) -> bool:
    return method.upper() in {"POST", "PUT", "PATCH", "DELETE"}


async def validate_csrf(request: Request) -> None:
    """Validate CSRF using Double-Submit Cookie pattern when enabled.
    Compares a readable CSRF cookie against a header for state-changing requests.
    No-op if disabled in settings.
    """
    if not settings.csrf_protection_enabled:
        return

    if not _is_state_changing(request.method):
        return

    # Allow login to proceed without CSRF (no session yet)
    if request.url.path.endswith("/api/v1/auth/login"):
        return

    cookie_name = settings.csrf_cookie_name
    header_name = settings.csrf_header_name

    csrf_cookie = request.cookies.get(cookie_name)
    csrf_header = request.headers.get(header_name)

    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="CSRF token missing or invalid")


async def get_bearer_or_cookie_token(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """Extract JWT token from Authorization header (Bearer) or from cookie.
    Preference: Authorization header > cookie.
    """
    if credentials and credentials.scheme.lower() == "bearer" and credentials.credentials:
        return credentials.credentials

    # Fallback to cookie
    token = request.cookies.get(getattr(settings, "cookie_name", "access_token"))
    if token:
        return token

    # No token found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
        token: str = Depends(get_bearer_or_cookie_token),
        db: AsyncSession = Depends(get_db)
) -> AppUser:
    """Get the current authenticated user from token in header or cookie."""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        jti: str = payload.get("jti")

        if email is None or jti is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Validate session
    session = await validate_session(db, jti)
    if not session:
        raise credentials_exception

    # Get user
    stmt = select(AppUser).where(AppUser.email == email, AppUser.is_active == True)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


# --- Opaque ID decoding dependency (Option B) ---

def decode_path_id(model: str) -> Callable[[str], int]:
    """
    Returns a dependency function to decode a URL-safe opaque ID into an integer PK.

    Example:
        @router.get("/users/{user_id}")
        async def get_user(user_id: int = Depends(decode_path_id("app_user"))):
            ...
    """
    async def _dep(eid: str = Path(..., description="Opaque ID")) -> int:
        try:
            return decode_id(model, eid)
        except OpaqueIdError:
            # Hide whether the ID exists
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return _dep


# --- Permission check dependency factory ---
from typing import Sequence, Union
from fastapi import HTTPException, Depends

async def _check_permission(
    permission_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> None:
    has = await user_has_permission(db, current_user.id, permission_code)
    if not has:
        # Mirror existing 403 semantics (see hospital_er endpoints)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Insufficient permissions: {permission_code}")


def require_permission(code: str):
    """
    Factory for a FastAPI dependency that ensures the current user has the given
    permission code. Usage:

        router = APIRouter(dependencies=[Depends(require_permission("HOSPITAL_ER"))])

    Or per-endpoint:

        @router.post("/items", dependencies=[Depends(require_permission("ITEMS.WRITE"))])
        async def create_item(...):
            ...
    """
    async def _dep(
        db: AsyncSession = Depends(get_db),
        current_user: AppUser = Depends(get_current_user),
    ) -> None:
        await _check_permission(code, db=db, current_user=current_user)

    return _dep
