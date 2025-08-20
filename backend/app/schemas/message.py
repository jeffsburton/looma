from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class MessageRead(OpaqueIdMixin):
    OPAQUE_MODEL = "message"
    id: int
    case_id: int
    person_id: int
    message: str
    reply_to_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    person_id: str
    message: str
    reply_to_id: Optional[str] = None
