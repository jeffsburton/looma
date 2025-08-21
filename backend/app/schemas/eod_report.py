from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class EodReportRead(OpaqueIdMixin):
    OPAQUE_MODEL = "eod_report"
    id: int
    case_id: int
    activity: Optional[str] = None
    communication: Optional[str] = None
    tomorrow_intel: Optional[str] = None
    tomorrow_ops: Optional[str] = None
    are_there_ministry_needs: bool
    ministry_needs: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EodReportUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    activity: Optional[str] = None
    communication: Optional[str] = None
    tomorrow_intel: Optional[str] = None
    tomorrow_ops: Optional[str] = None
    are_there_ministry_needs: Optional[bool] = None
    ministry_needs: Optional[str] = None
