from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RefStatusRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_status"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefStatusUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
