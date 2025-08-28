from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


class EventRead(OpaqueIdMixin):
    OPAQUE_MODEL = "event"
    id: int
    name: str
    city: str
    state_id: Optional[int] = None
    state_code: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    inactive: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("state_id")
    def _serialize_state_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("ref_value", int(v))


class EventUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    city: Optional[str] = None
    state_id: Optional[str] = None
    start: Optional[date] = None
    end: Optional[date] = None
    inactive: Optional[bool] = None
