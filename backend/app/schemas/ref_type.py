from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RefTypeRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_type"
    id: int
    name: str
    description: str
    code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RefTypeUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    code: Optional[str] = None
