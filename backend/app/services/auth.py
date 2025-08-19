from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.db.models.app_user import AppUser
from app.db.models.app_user_session import AppUserSession
from app.core.security import verify_password
from typing import Optional, Sequence, List, Union, overload


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[AppUser]:
    """Authenticate a user by email and password"""
    stmt = select(AppUser).where(AppUser.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user and verify_password(password, user.password_hash):
        return user
    return None


async def create_user_session(
        db: AsyncSession,
        user_id: int,
        jti: str,
        expires_minutes: int
) -> AppUserSession:
    """Create a new user session"""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=expires_minutes)

    session = AppUserSession(
        app_user_id=user_id,
        jti=jti,
        expires_at=expires_at,
        last_used_at=now,
        is_active=True
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def validate_session(db: AsyncSession, jti: str) -> Optional[AppUserSession]:
    """Validate and update session activity"""
    stmt = select(AppUserSession).where(
        AppUserSession.jti == jti,
        AppUserSession.is_active == True
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        return None

    now = datetime.now(timezone.utc)

    # Ensure session.expires_at is timezone-aware for comparison
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    # Check if session expired
    if expires_at < now:
        session.is_active = False
        await db.commit()
        return None

    # Update last used time
    session.last_used_at = now
    await db.commit()
    return session


async def invalidate_session(db: AsyncSession, jti: str) -> bool:
    """Invalidate a user session"""
    stmt = select(AppUserSession).where(AppUserSession.jti == jti)
    result = await db.execute(stmt)
    session = result.scalars().first()

    if session:
        session.is_active = False
        await db.commit()
        return True
    return False


async def cleanup_expired_sessions(db: AsyncSession, older_than_days: int = 7) -> int:
    """
    Delete expired sessions older than specified days.
    Returns the number of deleted sessions.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)

    stmt = delete(AppUserSession).where(
        AppUserSession.expires_at < cutoff_date
    )

    result = await db.execute(stmt)
    await db.commit()

    return await result.rowcount


async def extend_session(db: AsyncSession, jti: str, minutes: int) -> Optional[AppUserSession]:
    """Extend a session's expiry and update last_used_at. Returns the session if found and active."""
    stmt = select(AppUserSession).where(
        AppUserSession.jti == jti,
        AppUserSession.is_active == True
    )
    result = await db.execute(stmt)
    session = result.scalars().first()

    if not session:
        return None

    now = datetime.now(timezone.utc)
    session.expires_at = now + timedelta(minutes=minutes)
    session.last_used_at = now
    await db.commit()
    await db.refresh(session)
    return session




from sqlalchemy import select
from app.db.models.app_user_role import AppUserRole
from app.db.models.role_permission import RolePermission
from app.db.models.permission import Permission


async def get_user_permission_codes(db: AsyncSession, user_id: int) -> List[str]:
    """
    Return a list of all permission codes that the given user has via their roles.

    Joins across:
      app_user_role (user -> role) -> role_permission (role -> permission) -> permission (code)
    """
    stmt = (
        select(Permission.code)
        .select_from(AppUserRole)
        .join(RolePermission, RolePermission.role_id == AppUserRole.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(AppUserRole.app_user_id == user_id)
        .distinct()
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@overload
async def user_has_permission(db: AsyncSession, user_id: int, permission_code: str) -> bool: ...

@overload
async def user_has_permission(db: AsyncSession, user_id: int, permission_code: Sequence[str]) -> List[str]: ...

async def user_has_permission(
    db: AsyncSession,
    user_id: int,
    permission_code: Union[str, Sequence[str]]
) -> Union[bool, List[str]]:
    """
    Check whether a user has one or more permissions.

    - If `permission_code` is a single string, returns a bool indicating whether the
      user has that permission.
    - If `permission_code` is a sequence (list/tuple) of strings, performs a single
      SQL query using `Permission.code IN (...)` and returns the subset of codes the
      user actually has, preserving the input order and removing duplicates.

    Joins across:
      app_user_role (user -> role) -> role_permission (role -> permission) -> permission (code)
    """
    # Handle single permission (string)
    if isinstance(permission_code, str):
        stmt = (
            select(1)
            .select_from(AppUserRole)
            .join(RolePermission, RolePermission.role_id == AppUserRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                AppUserRole.app_user_id == user_id,
                Permission.code == permission_code,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.first() is not None

    # Handle multiple permissions (list/tuple of strings)
    # Protect against sequences that are not list/tuple; we only consider list/tuple as batch.
    if not isinstance(permission_code, (list, tuple)):
        # Fallback: treat as no permissions
        return []

    # Normalize input: remove falsy entries and deduplicate while preserving order
    seen = set()
    codes: List[str] = []
    for c in permission_code:
        if not c or not isinstance(c, str):
            continue
        if c not in seen:
            seen.add(c)
            codes.append(c)

    if not codes:
        return []

    stmt = (
        select(Permission.code)
        .select_from(AppUserRole)
        .join(RolePermission, RolePermission.role_id == AppUserRole.role_id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            AppUserRole.app_user_id == user_id,
            Permission.code.in_(codes),
        )
    )

    result = await db.execute(stmt)
    found_codes = set(result.scalars().all())

    # Preserve original order
    return [c for c in codes if c in found_codes]
