from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefRelationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_relation"
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class RefRelationUpsert(BaseModel):
    """
    Create or update a ref_relation row.
    """
    id: Optional[str] = None
    name: str
