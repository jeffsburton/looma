from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseVictimologyRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_victimology"
    id: int
    case_id: int
    victimology_id: int
    answer_id: Optional[int] = None
    details: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseVictimologyUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    victimology_id: str
    answer_id: Optional[str] = None
    details: Optional[str] = None
