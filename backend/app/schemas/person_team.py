from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class PersonTeamRead(OpaqueIdMixin):
    OPAQUE_MODEL = "person_team"
    id: int
    person_id: int
    team_id: int
    team_role_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonTeamUpsert(BaseModel):
    id: Optional[str] = None
    person_id: str
    team_id: str
    team_role_id: str
