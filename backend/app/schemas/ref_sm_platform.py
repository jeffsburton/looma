from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefSmPlatformRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_sm_platform"
    id: int
    name: str
    url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefSmPlatformUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    url: Optional[str] = None
