from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class CaseActionRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_action"
    id: int
    case_id: int
    action_id: int

    model_config = ConfigDict(from_attributes=True)


class CaseActionUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    action_id: str
