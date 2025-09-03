from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.schemas.mixins import OpaqueIdMixin


class CaseSearchUrgencyRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_search_urgency"
    id: int
    case_id: int
    age_id: Optional[int] = None
    physical_condition_id: Optional[int] = None
    medical_condition_id: Optional[int] = None
    personal_risk_id: Optional[int] = None
    online_risk_id: Optional[int] = None
    family_risk_id: Optional[int] = None
    behavioral_risk_id: Optional[int] = None
    score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseSearchUrgencyUpsert(BaseModel):
    id: Optional[str] = None
    case_id: Optional[str] = None
    age_id: Optional[str] = None
    physical_condition_id: Optional[str] = None
    medical_condition_id: Optional[str] = None
    personal_risk_id: Optional[str] = None
    online_risk_id: Optional[str] = None
    family_risk_id: Optional[str] = None
    behavioral_risk_id: Optional[str] = None
    # score is computed server-side and not accepted from client
