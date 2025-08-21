from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class IntelActivityRead(OpaqueIdMixin):
    OPAQUE_MODEL = "intel_activity"
    id: int
    case_id: int
    date: date
    entered_by_id: int
    what: Optional[str] = None
    source_id: Optional[int] = None
    source_other: Optional[str] = None
    findings: Optional[str] = None
    case_management: Optional[str] = None
    reported_to: Optional[int] = None
    on_eod_report: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntelActivityUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    date: date
    entered_by_id: str
    what: Optional[str] = None
    source_id: Optional[str] = None
    source_other: Optional[str] = None
    findings: Optional[str] = None
    case_management: Optional[str] = None
    reported_to: Optional[str] = None
    on_eod_report: Optional[bool] = None
