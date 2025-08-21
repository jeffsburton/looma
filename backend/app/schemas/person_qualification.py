from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PersonQualificationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "person_qualification"
    id: int
    person_id: int
    qualification_id: int
    date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonQualificationUpsert(BaseModel):
    id: Optional[str] = None
    person_id: str
    qualification_id: str
    date: Optional[date] = None
