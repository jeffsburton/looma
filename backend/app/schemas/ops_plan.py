import datetime as dt
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas.mixins import OpaqueIdMixin
from app.core.id_codec import encode_id


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
    date: Optional[dt.date] = None
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
    briefing_time: Optional[dt.time] = None
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
    created_at: dt.datetime
    updated_at: dt.datetime

    model_config = ConfigDict(from_attributes=True)

    # Encode foreign keys as opaque ids per guidelines
    @field_serializer("case_id")
    def _serialize_case_id(self, v: int) -> str:
        return encode_id("case", int(v))

    @field_serializer("created_by")
    def _serialize_created_by(self, v: int) -> str:
        return encode_id("person", int(v))

    @field_serializer("team_id")
    def _serialize_team_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("team", int(v))

    @field_serializer("op_type_id")
    def _serialize_op_type_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("responsible_agency_id")
    def _serialize_responsible_agency_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("organization", int(v))

    @field_serializer("subject_legal_id")
    def _serialize_subject_legal_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("comms_channel_id")
    def _serialize_comms_channel_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("hospital_er_id")
    def _serialize_hospital_er_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("hospital_er", int(v))

    @field_serializer("resp_contact_at_door_id")
    def _serialize_resp_contact_at_door_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    @field_serializer("resp_overwatch_id")
    def _serialize_resp_overwatch_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    @field_serializer("resp_navigation_id")
    def _serialize_resp_navigation_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    @field_serializer("resp_communications_id")
    def _serialize_resp_communications_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    @field_serializer("resp_safety_id")
    def _serialize_resp_safety_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    @field_serializer("resp_medical_id")
    def _serialize_resp_medical_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("person", int(v))

    # Threat ref-values
    @field_serializer("threat_dogs_id")
    def _serialize_threat_dogs_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("threat_cameras_id")
    def _serialize_threat_cameras_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("threat_weapons_id")
    def _serialize_threat_weapons_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("threat_drugs_id")
    def _serialize_threat_drugs_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("threat_gangs_id")
    def _serialize_threat_gangs_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))

    @field_serializer("threat_assault_id")
    def _serialize_threat_assault_id(self, v: Optional[int]) -> Optional[str]:
        return None if v is None else encode_id("ref_value", int(v))


class OpsPlanUpsert(BaseModel):
    id: Optional[str] = None
    case_id: Optional[str] = None
    created_by: Optional[str] = None
    forecast: Optional[str] = None
    temperature: Optional[int] = None
    humidity: Optional[int] = None
    precipitation: Optional[int] = None
    uv_index: Optional[int] = None
    winds: Optional[str] = None
    date: Optional[dt.date] = None
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
    briefing_time: Optional[dt.time] = None
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
