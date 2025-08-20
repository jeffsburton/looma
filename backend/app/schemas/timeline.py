from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class TimelineRead(OpaqueIdMixin):
    OPAQUE_MODEL = "timeline"
    id: int
    case_id: int
    person_id: int
    date: date
    time: Optional[time] = None
    who_id: Optional[int] = None
    what: Optional[str] = None
    details: Optional[str] = None
    where: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TimelineUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    person_id: str
    date: date
    time: Optional[time] = None
    who_id: Optional[str] = None
    what: Optional[str] = None
    details: Optional[str] = None
    where: Optional[str] = None
