from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PersonCaseRead(OpaqueIdMixin):
    OPAQUE_MODEL = "person_case"
    id: int
    person_id: int
    case_id: int
    relationship_id: Optional[int] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonCaseUpsert(BaseModel):
    id: Optional[str] = None
    person_id: str
    case_id: str
    relationship_id: Optional[str] = None
    relationship: Optional[str] = None
    notes: Optional[str] = None
