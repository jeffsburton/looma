from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PersonRead(OpaqueIdMixin):
    OPAQUE_MODEL = "person"
    id: int
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonUpsert(BaseModel):
    id: Optional[str] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    organization_id: Optional[str] = None
