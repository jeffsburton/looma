from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case"
    id: int
    subject_id: int
    date_missing: Optional[date] = None
    time_missing: Optional[time] = None
    number: Optional[str] = None
    missing_from_state_id: Optional[int] = None
    inactive: bool
    shepherds_contributed_intel: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseUpsert(BaseModel):
    """
    Payload for creating or updating a case.
    If `id` is provided (opaque), the record will be updated; otherwise, created.
    Foreign keys are passed in as opaque strings to be decoded in endpoints.
    """
    id: Optional[str] = None
    subject_id: str
    date_missing: Optional[date] = None
    time_missing: Optional[time] = None
    number: Optional[str] = None
    missing_from_state_id: Optional[str] = None
    inactive: Optional[bool] = None
