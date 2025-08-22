from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.mixins import OpaqueIdMixin


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    # collected but stored in onboarding_data JSON
    phone: Optional[str] = None
    organization: Optional[str] = None
    referred_by: Optional[str] = None
    # new field stored directly
    telegram: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    telegram: Optional[str] = None


class UserRead(OpaqueIdMixin):
    OPAQUE_MODEL = "app_user"
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    telegram: Optional[str] = None
    created_at: datetime
    updated_at: datetime