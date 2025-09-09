from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


class ReactionGroup(BaseModel):
    emoji: str
    count: int


class MessageRead(OpaqueIdMixin):
    """
    Response model for chat/case messages. Uses opaque IDs for id and selected foreign keys.
    """
    OPAQUE_MODEL = "message"

    # Core identifiers
    id: int
    case_id: int
    written_by_id: Optional[int] = None

    # Content
    message: str
    reply_to_id: Optional[int] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Augmented fields used by list/create endpoints
    writer_name: Optional[str] = None
    seen: Optional[bool] = None
    reaction: Optional[str] = None
    reactions: Optional[List[ReactionGroup]] = None
    reply_to_text: Optional[str] = None
    is_mine: Optional[bool] = None

    # UI helpers
    writer_photo_url: Optional[str] = None
    my_photo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    # Foreign key serializers
    @field_serializer("case_id")
    def _serialize_case_id(self, v: int) -> str:
        return encode_id("case", int(v))

    @field_serializer("written_by_id")
    def _serialize_written_by_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("person", int(v))

    @field_serializer("reply_to_id")
    def _serialize_reply_to_id(self, v: Optional[int]) -> Optional[str]:
        if v is None:
            return None
        return encode_id("message", int(v))
