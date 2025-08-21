from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class FileRead(OpaqueIdMixin):
    OPAQUE_MODEL = "file"
    id: int
    case_id: int
    file_name: str
    created_by_id: int
    source: Optional[str] = None
    notes: Optional[str] = None
    rfi_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    file_name: str
    created_by_id: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    rfi_id: Optional[str] = None
