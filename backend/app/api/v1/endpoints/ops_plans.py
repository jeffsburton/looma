from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.ops_plan import OpsPlan
from app.core.id_codec import decode_id, OpaqueIdError

from .case_utils import _decode_or_404, can_user_access_case
from app.schemas.ops_plan import OpsPlanRead, OpsPlanUpsert

router = APIRouter()


@router.post("/{case_id}/ops-plans", summary="Create an ops plan for a case", response_model=OpsPlanRead)
async def create_ops_plan(
    case_id: str,
    payload: OpsPlanUpsert | None = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Resolve created_by from current user's person
    from sqlalchemy import select
    from app.db.models.person import Person

    created_by_id = (
        await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))
    ).scalar_one_or_none()
    if created_by_id is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    row = OpsPlan(
        case_id=int(case_db_id),
        created_by=int(created_by_id),
    )

    # If client provided initial fields, apply (mirrors patch logic decode helper)
    if payload is not None:
        def _dec(model: str, val):
            if val is None:
                return None
            s = str(val)
            if s == "":
                return None
            if s.isdigit():
                return int(s)
            try:
                return int(decode_id(model, s))
            except Exception:
                return None
        row.forecast = payload.forecast
        row.temperature = payload.temperature
        row.humidity = payload.humidity
        row.precipitation = payload.precipitation
        row.uv_index = payload.uv_index
        row.winds = payload.winds
        row.date = payload.date
        row.team_id = _dec("team", payload.team_id)
        row.op_type_id = _dec("ref_value", payload.op_type_id)
        row.op_type_other = payload.op_type_other
        row.responsible_agency_id = _dec("organization", payload.responsible_agency_id)
        row.subject_legal_id = _dec("ref_value", payload.subject_legal_id)
        row.address = payload.address
        row.city = payload.city
        row.vehicles = payload.vehicles
        row.residence_owner = payload.residence_owner
        row.threat_dogs_id = _dec("ref_value", payload.threat_dogs_id)
        row.threat_cameras_id = _dec("ref_value", payload.threat_cameras_id)
        row.threat_weapons_id = _dec("ref_value", payload.threat_weapons_id)
        row.threat_drugs_id = _dec("ref_value", payload.threat_drugs_id)
        row.threat_gangs_id = _dec("ref_value", payload.threat_gangs_id)
        row.threat_assault_id = _dec("ref_value", payload.threat_assault_id)
        row.threat_other = payload.threat_other
        row.briefing_time = payload.briefing_time
        row.rendevouz_location = payload.rendevouz_location
        row.primary_location = payload.primary_location
        row.comms_channel_id = _dec("ref_value", payload.comms_channel_id)
        if payload.police_phone is not None:
            row.police_phone = payload.police_phone
        if payload.ems_phone is not None:
            row.ems_phone = payload.ems_phone
        row.hospital_er_id = _dec("hospital_er", payload.hospital_er_id)
        row.resp_contact_at_door_id = _dec("person", payload.resp_contact_at_door_id)
        row.resp_overwatch_id = _dec("person", payload.resp_overwatch_id)
        row.resp_navigation_id = _dec("person", payload.resp_navigation_id)
        row.resp_communications_id = _dec("person", payload.resp_communications_id)
        row.resp_safety_id = _dec("person", payload.resp_safety_id)
        row.resp_medical_id = _dec("person", payload.resp_medical_id)

    db.add(row)
    await db.commit()
    await db.refresh(row)

    return OpsPlanRead.model_validate(row)


@router.get("/{case_id}/ops-plans", summary="List ops plans for a case", response_model=List[OpsPlanRead])
async def list_ops_plans(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    rows = (
        await db.execute(
            select(OpsPlan).where(OpsPlan.case_id == int(case_db_id)).order_by(asc(OpsPlan.id))
        )
    ).scalars().all()

    return [OpsPlanRead.model_validate(r) for r in rows]


@router.get("/{case_id}/ops-plans/{ops_plan_id}", summary="Get an ops plan for a case", response_model=OpsPlanRead)
async def get_ops_plan(
    case_id: str,
    ops_plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        plan_db_id = int(decode_id("ops_plan", ops_plan_id)) if not str(ops_plan_id).isdigit() else int(ops_plan_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Ops Plan not found")

    row = (
        await db.execute(select(OpsPlan).where(OpsPlan.id == plan_db_id, OpsPlan.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Ops Plan not found")

    return OpsPlanRead.model_validate(row)


@router.patch("/{case_id}/ops-plans/{ops_plan_id}", summary="Update an ops plan for a case", response_model=OpsPlanRead)
async def update_ops_plan(
    case_id: str,
    ops_plan_id: str,
    payload: OpsPlanUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        plan_db_id = int(decode_id("ops_plan", ops_plan_id)) if not str(ops_plan_id).isdigit() else int(ops_plan_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Ops Plan not found")

    row = (
        await db.execute(select(OpsPlan).where(OpsPlan.id == int(plan_db_id), OpsPlan.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Ops Plan not found")

    # Determine which fields were provided
    fields_set = getattr(payload, "model_fields_set", set())

    # Helper to decode optional opaque ref ids; accept numeric ids as well
    def _dec(model: str, val: Optional[str]) -> Optional[int]:
        if val is None:
            return None
        s = str(val)
        if s == "":
            return None
        if s.isdigit():
            return int(s)
        try:
            return int(decode_id(model, s))
        except Exception:
            return None

    # Apply updates conditionally
    if "forecast" in fields_set:
        row.forecast = payload.forecast
    if "temperature" in fields_set:
        row.temperature = payload.temperature
    if "humidity" in fields_set:
        row.humidity = payload.humidity
    if "precipitation" in fields_set:
        row.precipitation = payload.precipitation
    if "uv_index" in fields_set:
        row.uv_index = payload.uv_index
    if "winds" in fields_set:
        row.winds = payload.winds
    if "date" in fields_set:
        row.date = payload.date
    if "team_id" in fields_set:
        row.team_id = _dec("team", payload.team_id)
    if "op_type_id" in fields_set:
        row.op_type_id = _dec("ref_value", payload.op_type_id)
    if "op_type_other" in fields_set:
        row.op_type_other = payload.op_type_other
    if "responsible_agency_id" in fields_set:
        row.responsible_agency_id = _dec("organization", payload.responsible_agency_id)
    if "subject_legal_id" in fields_set:
        row.subject_legal_id = _dec("ref_value", payload.subject_legal_id)
    if "address" in fields_set:
        row.address = payload.address
    if "city" in fields_set:
        row.city = payload.city
    if "vehicles" in fields_set:
        row.vehicles = payload.vehicles
    if "residence_owner" in fields_set:
        row.residence_owner = payload.residence_owner
    if "threat_dogs_id" in fields_set:
        row.threat_dogs_id = _dec("ref_value", payload.threat_dogs_id)
    if "threat_cameras_id" in fields_set:
        row.threat_cameras_id = _dec("ref_value", payload.threat_cameras_id)
    if "threat_weapons_id" in fields_set:
        row.threat_weapons_id = _dec("ref_value", payload.threat_weapons_id)
    if "threat_drugs_id" in fields_set:
        row.threat_drugs_id = _dec("ref_value", payload.threat_drugs_id)
    if "threat_gangs_id" in fields_set:
        row.threat_gangs_id = _dec("ref_value", payload.threat_gangs_id)
    if "threat_assault_id" in fields_set:
        row.threat_assault_id = _dec("ref_value", payload.threat_assault_id)
    if "threat_other" in fields_set:
        row.threat_other = payload.threat_other
    if "briefing_time" in fields_set:
        row.briefing_time = payload.briefing_time
    if "rendevouz_location" in fields_set:
        row.rendevouz_location = payload.rendevouz_location
    if "primary_location" in fields_set:
        row.primary_location = payload.primary_location
    if "comms_channel_id" in fields_set:
        row.comms_channel_id = _dec("ref_value", payload.comms_channel_id)
    if "police_phone" in fields_set:
        row.police_phone = payload.police_phone or row.police_phone
    if "ems_phone" in fields_set:
        row.ems_phone = payload.ems_phone or row.ems_phone
    if "hospital_er_id" in fields_set:
        row.hospital_er_id = _dec("hospital_er", payload.hospital_er_id)
    if "resp_contact_at_door_id" in fields_set:
        row.resp_contact_at_door_id = _dec("person", payload.resp_contact_at_door_id)
    if "resp_overwatch_id" in fields_set:
        row.resp_overwatch_id = _dec("person", payload.resp_overwatch_id)
    if "resp_navigation_id" in fields_set:
        row.resp_navigation_id = _dec("person", payload.resp_navigation_id)
    if "resp_communications_id" in fields_set:
        row.resp_communications_id = _dec("person", payload.resp_communications_id)
    if "resp_safety_id" in fields_set:
        row.resp_safety_id = _dec("person", payload.resp_safety_id)
    if "resp_medical_id" in fields_set:
        row.resp_medical_id = _dec("person", payload.resp_medical_id)

    await db.flush()
    await db.refresh(row)
    await db.commit()

    return OpsPlanRead.model_validate(row)
