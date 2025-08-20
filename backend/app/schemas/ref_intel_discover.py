from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin




class RefIntelDiscoverUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
