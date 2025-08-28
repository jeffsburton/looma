from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RfiSourceRead(OpaqueIdMixin):
    OPAQUE_MODEL = "rfi_source"
    id: int
    name: str
    description: str
    # For reads, expose opaque person IDs (or None) for selection widgets
    primary_id: Optional[str] = None
    backup_id: Optional[str] = None
    # Also provide friendly display names joined from Person
    primary_name: Optional[str] = None
    backup_name: Optional[str] = None
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RfiSourceUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    description: str
    # Accept opaque person IDs
    primary_id: Optional[str] = None
    backup_id: Optional[str] = None
    inactive: Optional[bool] = None
