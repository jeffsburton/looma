from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class FilePersonRead(OpaqueIdMixin):
    OPAQUE_MODEL = "file_person"
    id: int
    file_id: int
    person_id: int
    case_photo: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilePersonUpsert(BaseModel):
    id: Optional[str] = None
    file_id: str
    person_id: str
    case_photo: Optional[bool] = None