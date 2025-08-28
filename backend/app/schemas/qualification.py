from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class QualificationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "qualification"
    id: int
    name: str
    description: Optional[str] = None
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QualificationUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    inactive: Optional[bool] = None
