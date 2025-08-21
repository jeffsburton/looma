from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseManagementRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_management"
    id: int
    case_id: int
    consent_sent: bool
    consent_returned: bool
    flyer_complete: bool
    ottic: bool
    csec_id: Optional[int] = None
    missing_status_id: Optional[int] = None
    classification_id: Optional[int] = None
    ncic_case_number: Optional[str] = None
    ncmec_case_number: Optional[str] = None
    le_case_number: Optional[str] = None
    le_24hour_contact: Optional[str] = None
    ss_case_number: Optional[str] = None
    ss_24hour_contact: Optional[str] = None
    jpo_case_number: Optional[str] = None
    jpo_24hour_contact: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseManagementUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    consent_sent: Optional[bool] = None
    consent_returned: Optional[bool] = None
    flyer_complete: Optional[bool] = None
    ottic: Optional[bool] = None
    csec_id: Optional[str] = None
    missing_status_id: Optional[str] = None
    classification_id: Optional[str] = None
    ncic_case_number: Optional[str] = None
    ncmec_case_number: Optional[str] = None
    le_case_number: Optional[str] = None
    le_24hour_contact: Optional[str] = None
    ss_case_number: Optional[str] = None
    ss_24hour_contact: Optional[str] = None
    jpo_case_number: Optional[str] = None
    jpo_24hour_contact: Optional[str] = None
