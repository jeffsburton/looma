from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class SocialMediaAliasRead(OpaqueIdMixin):
    OPAQUE_MODEL = "social_media_alias"
    id: int
    social_media_id: int
    alias_status_id: int
    alias: Optional[str] = None
    alias_owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialMediaAliasUpsert(BaseModel):
    id: Optional[str] = None
    social_media_id: str
    alias_status_id: str
    alias: Optional[str] = None
    alias_owner_id: Optional[str] = None
