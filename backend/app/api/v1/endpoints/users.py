from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user import get_user_by_email, create_user

# IMPORTANT - protects all endpoints in this file.
router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_new_user(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)

):
    """Create a new user"""
    # Check if user already exists
    existing_user = await get_user_by_email(db, str(user_data.email))
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = await create_user(db, user_data)
    return user