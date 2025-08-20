from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class SubjectRead(OpaqueIdMixin):
    OPAQUE_MODEL = "subject"
    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubjectUpsert(BaseModel):
    """
    Payload for creating or updating a subject.
    If `id` is provided (opaque), the record will be updated; otherwise, created.
    """
    id: Optional[str] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
