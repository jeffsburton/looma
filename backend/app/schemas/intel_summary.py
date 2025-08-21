from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class IntelSummaryRead(OpaqueIdMixin):
    OPAQUE_MODEL = "intel_summary"
    id: int
    case_id: int
    date: date
    entered_by_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntelSummaryUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    date: date
    entered_by_id: str
