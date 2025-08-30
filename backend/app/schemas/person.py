from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


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

    @field_serializer("organization_id")
    def _serialize_org_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("organization", int(v))


class PersonUpsert(BaseModel):
    id: Optional[str] = None
    first_name: str
    last_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    organization_id: Optional[str] = None
