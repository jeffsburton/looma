from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class HospitalErRead(OpaqueIdMixin):
    OPAQUE_MODEL = "hospital_er"
    id: int
    name: str
    address: str
    city: str
    state_id: int
    zip_code: str
    phone: str
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HospitalErUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    address: str
    city: str
    state_id: str
    zip_code: str
    phone: str
    inactive: Optional[bool] = None
