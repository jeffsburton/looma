from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class OrganizationRead(BaseModel):
    id: int
    name: str
    main_contact_id: Optional[int] = None
    ref_state_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
