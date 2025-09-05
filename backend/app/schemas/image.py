from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class ImageRead(OpaqueIdMixin):
    OPAQUE_MODEL = "image"
    id: int
    case_id: int
    file_name: str
    created_by_id: Optional[int] = None
    source_url: Optional[str] = None
    where: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    storage_slug: Optional[str] = None
    rfi_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    mime_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ImageUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    file_name: str
    created_by_id: Optional[str] = None
    source_url: Optional[str] = None
    where: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    storage_slug: Optional[str] = None
    rfi_id: Optional[str] = None
