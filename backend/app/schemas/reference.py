from pydantic import BaseModel, ConfigDict
from app.schemas.mixins import OpaqueIdMixin


class StateRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ref_value"
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)
