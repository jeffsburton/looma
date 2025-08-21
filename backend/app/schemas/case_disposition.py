from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseDispositionRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_disposition"
    id: int
    case_id: int
    shepherds_contributed_intel: bool
    date_found: Optional[date] = None
    scope_id: Optional[int] = None
    class_id: Optional[int] = None
    status_id: Optional[int] = None
    living_id: Optional[int] = None
    found_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseDispositionUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    shepherds_contributed_intel: Optional[bool] = None
    date_found: Optional[date] = None
    scope_id: Optional[str] = None
    class_id: Optional[str] = None
    status_id: Optional[str] = None
    living_id: Optional[str] = None
    found_by_id: Optional[str] = None
