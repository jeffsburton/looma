from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RoleRead(OpaqueIdMixin):
    OPAQUE_MODEL = "role"
    id: int
    name: str
    code: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    description: Optional[str] = None
