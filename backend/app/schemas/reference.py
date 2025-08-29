from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.mixins import OpaqueIdMixin


class StateRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_value"
    id: int
    name: str
    code: str
    sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RefValueRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_value"
    id: int
    name: str
    description: str
    code: str
    inactive: bool
    num_value: Optional[int] = None
    sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RefValueCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = ""
    inactive: Optional[bool] = False
    num_value: Optional[int] = None
    sort_order: Optional[int] = None
