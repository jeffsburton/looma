from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RefFoundByRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_found_by"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefFoundByUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
