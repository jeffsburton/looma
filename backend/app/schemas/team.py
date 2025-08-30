from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin


class TeamMemberSummary(BaseModel):
    id: int
    name: str
    photo_url: Optional[str] = None
    role_name: Optional[str] = None
    role_id: Optional[str] = None  # opaque ref_value id for TEAM_ROLE
    role_code: Optional[str] = None
    # Contact info (optional; included for convenience in team listing)
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None

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

    @field_serializer("event_id")
    def _serialize_event_id(self, v: Optional[int]) -> Optional[str]:
        from app.core.id_codec import encode_id
        if v is None:
            return None
        return encode_id("event", int(v))


class TeamUpsert(BaseModel):
    id: Optional[str] = None
    name: str
    inactive: Optional[bool] = None
    event_id: Optional[str] = None
