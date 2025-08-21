from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RfiSourceRead(OpaqueIdMixin):
    OPAQUE_MODEL = "rfi_source"
    id: int
    name: str
    description: str
    primary_id: int
    backup_id: int
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RfiSourceUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    primary_id: str
    backup_id: str
    inactive: Optional[bool] = None
