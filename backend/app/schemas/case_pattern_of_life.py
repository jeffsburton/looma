from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CasePatternOfLifeRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_pattern_of_life"
    id: int
    case_id: int
    school: Optional[str] = None
    grade: Optional[str] = None
    missing_classes: bool
    school_laptop: bool
    school_laptop_taken: bool
    school_address: Optional[str] = None
    employed: bool
    employer: Optional[str] = None
    work_hours: Optional[str] = None
    employer_address: Optional[str] = None
    confidants: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CasePatternOfLifeUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    school: Optional[str] = None
    grade: Optional[str] = None
    missing_classes: Optional[bool] = None
    school_laptop: Optional[bool] = None
    school_laptop_taken: Optional[bool] = None
    school_address: Optional[str] = None
    employed: Optional[bool] = None
    employer: Optional[str] = None
    work_hours: Optional[str] = None
    employer_address: Optional[str] = None
    confidants: Optional[str] = None
