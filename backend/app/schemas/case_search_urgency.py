from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class CaseSearchUrgencyRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_search_urgency"
    id: int
    case_id: int
    age_id: int
    physical_condition_id: int
    medical_condition_id: int
    personal_risk_id: int
    online_risk_id: int
    family_risk_id: int
    behavioral_risk_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseSearchUrgencyUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    age_id: str
    physical_condition_id: str
    medical_condition_id: str
    personal_risk_id: str
    online_risk_id: str
    family_risk_id: str
    behavioral_risk_id: str
