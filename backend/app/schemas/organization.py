from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime
from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


class OrganizationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "organization"
    id: int
    name: str
    state_id: Optional[int] = None
    state_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("state_id")
    def _serialize_state_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("ref_value", int(v))


class OrganizationUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    state_id: Optional[str] = None
