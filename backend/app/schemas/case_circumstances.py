from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.mixins import OpaqueIdMixin


class CaseCircumstancesRead(OpaqueIdMixin):
    OPAQUE_MODEL = "case_circumstances"
    id: int
    case_id: int
    action_id: int
    date_missing: Optional[datetime] = None
    time_missing: Optional[datetime] = None
    date_reported: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[int] = None
    point_last_seen: Optional[str] = None
    have_id_id: Optional[int] = None
    id_taken_id: Optional[int] = None
    have_money_id: Optional[int] = None
    money_taken_id: Optional[int] = None
    have_cc_id: Optional[int] = None
    cc_taken_id: Optional[int] = None
    vehicle_taken: bool
    vehicle_desc: Optional[str] = None
    with_whom: Optional[str] = None
    what_happened: Optional[str] = None
    clothing_top: Optional[str] = None
    clothing_bottom: Optional[str] = None
    clothing_shoes: Optional[str] = None
    clothing_outerwear: Optional[str] = None
    clothing_innerwear: Optional[str] = None
    bags: Optional[str] = None
    other_items: Optional[str] = None
    mobile_carrier_id: Optional[int] = None
    mobile_carrier_other: Optional[str] = None
    voip_id: Optional[int] = None
    wifi_only: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseCircumstancesUpsert(BaseModel):
    id: Optional[str] = None
    case_id: str
    action_id: str
    date_missing: Optional[datetime] = None
    time_missing: Optional[datetime] = None
    date_reported: Optional[datetime] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state_id: Optional[str] = None
    point_last_seen: Optional[str] = None
    have_id_id: Optional[str] = None
    id_taken_id: Optional[str] = None
    have_money_id: Optional[str] = None
    money_taken_id: Optional[str] = None
    have_cc_id: Optional[str] = None
    cc_taken_id: Optional[str] = None
    vehicle_taken: Optional[bool] = None
    vehicle_desc: Optional[str] = None
    with_whom: Optional[str] = None
    what_happened: Optional[str] = None
    clothing_top: Optional[str] = None
    clothing_bottom: Optional[str] = None
    clothing_shoes: Optional[str] = None
    clothing_outerwear: Optional[str] = None
    clothing_innerwear: Optional[str] = None
    bags: Optional[str] = None
    other_items: Optional[str] = None
    mobile_carrier_id: Optional[str] = None
    mobile_carrier_other: Optional[str] = None
    voip_id: Optional[str] = None
    wifi_only: Optional[bool] = None
