from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.app_user import AppUser
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from typing import Optional
import json


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[AppUser]:
    """Get user by email"""
    stmt = select(AppUser).where(AppUser.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[AppUser]:
    """Get user by ID"""
    stmt = select(AppUser).where(AppUser.id == user_id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def create_user(db: AsyncSession, user_data: UserCreate) -> AppUser:
    """Create a new user.

    - Only persist columns that exist on app_user (email, password_hash, is_active, onboarding_data).
    - Collect other form fields into onboarding_data JSON.
    - Attach transient attributes (first_name, last_name, telegram, phone) to the returned instance
      so immediate response serialization and notifications can still access them.
    """
    hashed_password = get_password_hash(user_data.password)

    # Collect onboarding fields that are not stored as columns on app_user
    onboarding: dict = {}
    if getattr(user_data, "first_name", None):
        onboarding["first_name"] = user_data.first_name
    if getattr(user_data, "last_name", None):
        onboarding["last_name"] = user_data.last_name
    if getattr(user_data, "phone", None):
        onboarding["phone"] = user_data.phone
    if getattr(user_data, "organization", None):
        onboarding["organization"] = user_data.organization
    if getattr(user_data, "referred_by", None):
        onboarding["referred_by"] = user_data.referred_by
    if getattr(user_data, "telegram", None):
        onboarding["telegram"] = user_data.telegram

    user = AppUser(
        email=str(user_data.email),
        password_hash=hashed_password,
        is_active=True,
        onboarding_data=json.dumps(onboarding) if onboarding else None,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Attach transient attributes for compatibility with response models/notifications
    try:
        user.first_name = getattr(user_data, "first_name", None)
        user.last_name = getattr(user_data, "last_name", None)
        user.telegram = getattr(user_data, "telegram", None)
        user.phone = getattr(user_data, "phone", None)
    except Exception:
        # Best-effort; if SQLAlchemy disallows setting, ignore.
        pass

    return user