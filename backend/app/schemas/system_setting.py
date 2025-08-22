from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class SystemSettingRead(OpaqueIdMixin):
    OPAQUE_MODEL = "system_setting"

    id: int
    name: str
    value: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemSettingUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    value: str
