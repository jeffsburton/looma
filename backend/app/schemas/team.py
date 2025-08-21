from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class TeamRead(OpaqueIdMixin):
    OPAQUE_MODEL = "team"
    id: int
    name: str
    inactive: bool
    event_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    inactive: Optional[bool] = None
    event_id: Optional[str] = None
