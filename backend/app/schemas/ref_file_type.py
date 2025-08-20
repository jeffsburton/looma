from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefFileTypeRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_file_type"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefFileTypeUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
