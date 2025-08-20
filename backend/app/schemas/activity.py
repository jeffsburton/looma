from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class ActivityRead(OpaqueIdMixin):
    OPAQUE_MODEL = "activity"
    id: int
    case_id: int
    person_id: int
    date: date
    source: Optional[str] = None
    regarding_id: Optional[int] = None
    findings: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    person_id: str
    date: date
    source: Optional[str] = None
    regarding_id: Optional[str] = None
    findings: Optional[str] = None
