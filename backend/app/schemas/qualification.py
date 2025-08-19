from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class QualificationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "qualification"
    id: int
    name: str
    code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QualificationUpsert(BaseModel):
    """
    Payload for creating or updating a qualification.
    If `id` is provided (opaque), the record will be updated; otherwise, created.
    """
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
