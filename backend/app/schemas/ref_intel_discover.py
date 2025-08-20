from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RefIntelDiscoverRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_intel_discover"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefIntelDiscoverUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
