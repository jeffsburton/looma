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
    """Create a new user"""
    hashed_password = get_password_hash(user_data.password)

    onboarding: dict = {}
    if getattr(user_data, "phone", None):
        onboarding["phone"] = user_data.phone
    if getattr(user_data, "organization", None):
        onboarding["organization"] = user_data.organization
    if getattr(user_data, "referred_by", None):
        onboarding["referred_by"] = user_data.referred_by

    user = AppUser(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=str(user_data.email),
        password_hash=hashed_password,
        is_active=True,
        telegram=getattr(user_data, "telegram", None),
        onboarding_data=json.dumps(onboarding) if onboarding else None,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user