from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.mixins import OpaqueIdMixin


class OrganizationRead(OpaqueIdMixin):
    OPAQUE_MODEL = "organization"
    id: int
    name: str
    main_contact_id: Optional[int] = None
    ref_state_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
