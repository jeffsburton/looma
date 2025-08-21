from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class VictimologyRead(OpaqueIdMixin):
    OPAQUE_MODEL = "victimology"
    id: int
    victimology_category_id: int
    question: str
    follow_up: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VictimologyUpsert(BaseModel):
    id: Optional[str] = None
    victimology_category_id: str
    question: str
    follow_up: Optional[str] = None
