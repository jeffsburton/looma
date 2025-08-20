from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefActivityRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_activity"
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RefActivityUpsert(BaseModel):
    id: Optional[str] = None
    name: str
