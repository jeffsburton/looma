from datetime import datetime, date, time
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class OpsPlanRead(OpaqueIdMixin):
    OPAQUE_MODEL = "ops_plan"
    id: int
    case_id: int
    created_by: int
    forecast: Optional[str] = None
    temperature: Optional[int] = None
    humidity: Optional[int] = None
    precipitation: Optional[int] = None
    uv_index: Optional[int] = None
    winds: Optional[str] = None
    date: Optional[date] = None
    team_id: Optional[int] = None
    op_type_id: Optional[int] = None
    op_type_other: Optional[str] = None
    responsible_agency_id: Optional[int] = None
    subject_legal_id: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    vehicles: Optional[str] = None
    residence_owner: Optional[str] = None
    threat_dogs_id: Optional[int] = None
    threat_cameras_id: Optional[int] = None
    threat_weapons_id: Optional[int] = None
    threat_drugs_id: Optional[int] = None
    threat_gangs_id: Optional[int] = None
    threat_assault_id: Optional[int] = None
    threat_other: Optional[str] = None
    briefing_time: Optional[time] = None
    rendevouz_location: Optional[str] = None
    primary_location: Optional[str] = None
    comms_channel_id: Optional[int] = None
    police_phone: str
    ems_phone: str
    hospital_er_id: Optional[int] = None
    resp_contact_at_door_id: Optional[int] = None
    resp_overwatch_id: Optional[int] = None
    resp_navigation_id: Optional[int] = None
    resp_communications_id: Optional[int] = None
    resp_safety_id: Optional[int] = None
    resp_medical_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OpsPlanUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    created_by: str
    forecast: Optional[str] = None
    temperature: Optional[int] = None
    humidity: Optional[int] = None
    precipitation: Optional[int] = None
    uv_index: Optional[int] = None
    winds: Optional[str] = None
    date: Optional[date] = None
    team_id: Optional[str] = None
    op_type_id: Optional[str] = None
    op_type_other: Optional[str] = None
    responsible_agency_id: Optional[str] = None
    subject_legal_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    vehicles: Optional[str] = None
    residence_owner: Optional[str] = None
    threat_dogs_id: Optional[str] = None
    threat_cameras_id: Optional[str] = None
    threat_weapons_id: Optional[str] = None
    threat_drugs_id: Optional[str] = None
    threat_gangs_id: Optional[str] = None
    threat_assault_id: Optional[str] = None
    threat_other: Optional[str] = None
    briefing_time: Optional[time] = None
    rendevouz_location: Optional[str] = None
    primary_location: Optional[str] = None
    comms_channel_id: Optional[str] = None
    police_phone: Optional[str] = None
    ems_phone: Optional[str] = None
    hospital_er_id: Optional[str] = None
    resp_contact_at_door_id: Optional[str] = None
    resp_overwatch_id: Optional[str] = None
    resp_navigation_id: Optional[str] = None
    resp_communications_id: Optional[str] = None
    resp_safety_id: Optional[str] = None
    resp_medical_id: Optional[str] = None
