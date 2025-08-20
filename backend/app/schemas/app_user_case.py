from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class AppUserCaseRead(OpaqueIdMixin):
    OPAQUE_MODEL = "app_user_case"
    id: int
    app_user_id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppUserCaseUpsert(BaseModel):
    """
    Payload for creating or updating an app_user_case association.
    If `id` is provided (opaque), the record will be updated; otherwise, created.
    Foreign keys are expected as opaque IDs.
    """
    id: Optional[str] = None
    app_user_id: str
    case_id: str
