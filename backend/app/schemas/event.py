from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class EventRead(OpaqueIdMixin):
    OPAQUE_MODEL = "event"
    id: int
    case_id: int
    name: str
    city: str
    state_id: Optional[int] = None
    start: Optional[date] = None
    end: Optional[date] = None
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    name: str
    city: Optional[str] = None
    state_id: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    inactive: Optional[bool] = None
