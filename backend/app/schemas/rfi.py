from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RfiRead(OpaqueIdMixin):
    OPAQUE_MODEL = "rfi"
    id: int
    case_id: int
    name: str
    description: str
    created_by: int
    rfi_source_id: int
    subject_id: int
    details: Optional[str] = None
    responded_by_id: Optional[int] = None
    results: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RfiUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    name: str
    description: str
    created_by: str
    rfi_source_id: str
    subject_id: str
    details: Optional[str] = None
    responded_by_id: Optional[str] = None
    results: Optional[str] = None
