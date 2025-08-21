from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class AppUserSessionRead(OpaqueIdMixin):
    OPAQUE_MODEL = "app_user_session"
    id: int
    app_user_id: int
    jti: str
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AppUserSessionUpsert(BaseModel):
    id: Optional[str] = None
    app_user_id: str
    jti: str
    last_used_at: Optional[datetime] = None
    expires_at: datetime
    is_active: Optional[bool] = None
