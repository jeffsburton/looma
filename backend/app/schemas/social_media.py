from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class SocialMediaRead(OpaqueIdMixin):
    OPAQUE_MODEL = "social_media"
    id: int
    case_id: int
    person_id: Optional[int] = None
    account: str
    platform_id: int
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialMediaUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    person_id: Optional[str] = None
    account: str
    platform_id: str
    notes: Optional[str] = None
