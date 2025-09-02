from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseDemographicsRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_demographics"
    id: int
    case_id: int
    date_of_birth: Optional[date] = None
    age_when_missing: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    hair_color: Optional[str] = None
    hair_length: Optional[str] = None
    eye_color: Optional[str] = None
    identifying_marks: Optional[str] = None
    sex_id: Optional[int] = None
    race_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseDemographicsUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    date_of_birth: Optional[date] = None
    age_when_missing: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    hair_color: Optional[str] = None
    hair_length: Optional[str] = None
    eye_color: Optional[str] = None
    identifying_marks: Optional[str] = None
    sex_id: Optional[str] = None
    race_id: Optional[str] = None
