from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class FilePersonRead(OpaqueIdMixin):
    OPAQUE_MODEL = "image_person"
    id: int
    image_id: int
    subject_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FilePersonUpsert(BaseModel):
    id: Optional[str] = None
    image_id: str
    subject_id: str