from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class EventHospitalErRead(OpaqueIdMixin):
    OPAQUE_MODEL = "event_hospital_er"
    id: int
    event_id: int
    hospital_er_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventHospitalErUpsert(BaseModel):
    id: Optional[str] = None
    event_id: str
    hospital_er_id: str
