from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


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

    @field_serializer("state_id")
    def _serialize_state_id(self, v: int) -> str:
        # encode ref_value as opaque id for frontend forms
        return encode_id("ref_value", int(v))


class HospitalErUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    address: str
    city: str
    state_id: str
    zip_code: str
    phone: str
    inactive: Optional[bool] = None
