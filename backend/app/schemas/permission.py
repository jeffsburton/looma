from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PermissionRead(OpaqueIdMixin):
    OPAQUE_MODEL = "permission"
    id: int
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PermissionUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
