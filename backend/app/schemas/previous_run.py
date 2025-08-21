from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PreviousRunRead(OpaqueIdMixin):
    OPAQUE_MODEL = "previous_run"
    id: int
    case_id: int
    date_ran: date
    point_last_seen: Optional[str] = None
    accompanied_by: Optional[str] = None
    found_by: Optional[str] = None
    date_found: Optional[date] = None
    location_found: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreviousRunUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    date_ran: date
    point_last_seen: Optional[str] = None
    accompanied_by: Optional[str] = None
    found_by: Optional[str] = None
    date_found: Optional[date] = None
    location_found: Optional[str] = None
    notes: Optional[str] = None
