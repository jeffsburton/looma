from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefScopeRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_scope"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefScopeUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
