from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class TeamCaseRead(OpaqueIdMixin):
    OPAQUE_MODEL = "team_case"
    id: int
    team_id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamCaseUpsert(BaseModel):
    """
    Payload for creating or updating a team_case association.
    If `id` is provided (opaque), the record will be updated; otherwise, created.
    Foreign keys are expected as opaque IDs.
    """
    id: Optional[str] = None
    team_id: str
    case_id: str
