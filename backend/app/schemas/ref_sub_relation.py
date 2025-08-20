from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class RefSubRelationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_sub_relation"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefSubRelationUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
