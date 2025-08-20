from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class RefCaseClassificationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_case_classification"
    id: int
    name: str
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RefCaseClassificationUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    code: Optional[str] = None
