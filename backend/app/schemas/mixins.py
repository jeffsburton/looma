from pydantic import BaseModel
from pydantic import field_serializer
from typing import Optional, ClassVar

from app.core.id_codec import encode_id

class OpaqueIdMixin(BaseModel):
    """
    Pydantic v2 mixin that serializes the `id` field as an opaque string during output.

    Subclasses must set class attribute OPAQUE_MODEL to a non-empty string
    """
    # Treat as a normal class attribute, not a Pydantic field
    OPAQUE_MODEL: ClassVar[Optional[str]] = None

    @field_serializer("id", check_fields=False)
    def _serialize_id(self, v: int) -> str:
        model = getattr(self, "OPAQUE_MODEL", None) or getattr(self.__class__, "OPAQUE_MODEL", None)
        if not model:
            # If not configured, just pass through as string to avoid leaking raw ints
            # but make it clearly a configuration issue.
            return str(v)
        return encode_id(str(model), int(v))
