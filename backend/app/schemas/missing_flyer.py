from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class MissingFlyerRead(OpaqueIdMixin):
    OPAQUE_MODEL = "missing_flyer"
    id: int
    case_id: int
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MissingFlyerUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    created_by: str
