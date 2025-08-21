from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class OpsPlanAssignmentRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ops_plan_assignment"
    id: int
    ops_plan_id: int
    person_id: int
    role_id: int
    role_other: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpsPlanAssignmentUpsert(BaseModel):
    id: Optional[str] = None
    ops_plan_id: str
    person_id: str
    role_id: str
    role_other: Optional[str] = None
