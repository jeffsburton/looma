from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class TeamMemberSummary(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TeamCaseSummary(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TeamRead(OpaqueIdMixin):
    OPAQUE_MODEL = "team"
    id: int
    name: str
    inactive: bool
    event_id: Optional[int] = None
    event_name: Optional[str] = None
    photo_url: Optional[str] = None
    members: List[TeamMemberSummary] = []
    cases: List[TeamCaseSummary] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TeamUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    inactive: Optional[bool] = None
    event_id: Optional[str] = None
