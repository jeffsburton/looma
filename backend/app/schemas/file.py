from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class FileRead(OpaqueIdMixin):
    OPAQUE_MODEL = "file"
    id: int
    file_name: str
    created_by_id: Optional[int] = None
    source: Optional[str] = None
    where: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUpsert(BaseModel):
    id: Optional[str] = None
    file_name: str
    created_by_id: Optional[str] = None
    source: Optional[str] = None
    where: Optional[str] = None
    notes: Optional[str] = None
