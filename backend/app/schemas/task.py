from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


class TaskRead(OpaqueIdMixin):
    """
    Response model for case tasks. Uses opaque IDs for id and selected foreign keys.
    """
    OPAQUE_MODEL = "task"

    # Core identifiers
    id: int
    case_id: int
    assigned_by_id: Optional[int] = None

    # Content
    title: str
    description: str
    response: Optional[str] = None

    # Status
    ready_for_review: bool = False
    completed: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # UI sugar
    name: Optional[str] = None  # mirrors title for convenience in clients expecting `name`

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("case_id")
    def _serialize_case_id(self, v: int) -> str:
        return encode_id("case", int(v))

    @field_serializer("assigned_by_id")
    def _serialize_assigned_by_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("person", int(v))

    @field_serializer("name")
    def _serialize_name(self, v: Optional[str], info):  # type: ignore[override]
        # Always mirror from title if not explicitly set
        title = getattr(self, "title", None)
        return v if v is not None else title


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_by_id: Optional[str] = None  # opaque person id, optional; defaults to current user person


class TaskPartial(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    response: Optional[str] = None
    ready_for_review: Optional[bool] = None
    completed: Optional[bool] = None
    assigned_by_id: Optional[str] = None  # opaque person id
