from operator import truediv
from typing import List, Optional
from datetime import date as Date

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc, exists, or_, and_
import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.case import Case
from app.db.models.subject import Subject
from app.db.models.app_user_case import AppUserCase
from app.db.models.person import Person
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.services.auth import user_has_permission
from app.db.models.app_user import AppUser
from app.db.models.case_demographics import CaseDemographics
from app.db.models.case_circumstances import CaseCircumstances
from app.db.models.case_management import CaseManagement
from app.db.models.case_pattern_of_life import CasePatternOfLife
from app.db.models.ref_value import RefValue
from app.db.models.case_disposition import CaseDisposition
from app.db.models.case_exploitation import CaseExploitation
from app.db.models.case_victimology import CaseVictimology
from app.db.models.victimology import victimology as Victimology
from app.db.models.victimology_category import victimologyCategory as VictimologyCategory
from app.db.models.case_search_urgency import CaseSearchUrgency
from app.schemas.case_search_urgency import CaseSearchUrgencyUpsert
from app.schemas.case_demographics import CaseDemographicsUpsert
from app.schemas.case_management import CaseManagementUpsert
from app.schemas.case_pattern_of_life import CasePatternOfLifeUpsert
from app.schemas.case_circumstances import CaseCircumstancesUpsert



router = APIRouter(prefix="/cases")

# Include subrouters for modularized route groups
from . import files as _case_files
from . import messages as _case_messages
from . import timeline as _case_timeline
from . import activity as _case_activity
from . import social_media as _case_social_media
from . import case_persons as _case_persons
from . import case_subjects as _case_subjects
from . import tasks as _case_tasks

router.include_router(_case_files.router)
router.include_router(_case_messages.router)
router.include_router(_case_timeline.router)
router.include_router(_case_activity.router)
router.include_router(_case_social_media.router)
router.include_router(_case_persons.router)
router.include_router(_case_subjects.router)
router.include_router(_case_tasks.router)

# ---------- Helper utilities ----------

def _decode_or_404(model: str, opaque_id: str) -> int:
    # Accept numeric IDs directly as a convenience in internal calls
    if str(opaque_id).isdigit():
        return int(opaque_id)
    try:
        return decode_id(model, opaque_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail=f"{model.replace('_', ' ').title()} not found")


async def can_user_access_case(db: AsyncSession, user_id: int, case_id: int) -> bool:
    """
    Returns True if the user can access the given case based on:
      - Direct assignment via app_user_case
      - Team membership via person -> person_team -> team_case
    """
    # Direct assignment exists
    direct_exists = (
        await db.execute(
            select(1).where(and_(AppUserCase.app_user_id == user_id, AppUserCase.case_id == case_id)).limit(1)
        )
    ).first() is not None

    if direct_exists:
        return True

    # Team-based assignment exists
    team_exists_stmt = (
        select(1)
        .select_from(Person)
        .join(PersonTeam, PersonTeam.person_id == Person.id)
        .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
        .where(and_(Person.app_user_id == user_id, TeamCase.case_id == case_id))
        .limit(1)
    )

    team_exists = (await db.execute(team_exists_stmt)).first() is not None
    if team_exists:
        return True

    if user_has_permission(db, user_id, "CASES.ALL_CASES"):
        return True
    else:
        return False


@router.get("/select", summary="List active cases for selection")
async def list_cases_for_select(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Build base query: Only active cases
    q = (
        select(
            Case.id.label("case_id"),
            Case.case_number,
            Subject.id.label("subject_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.profile_pic.isnot(None).label("has_pic"),
        )
        .join(Subject, Subject.id == Case.subject_id)
        .where(Case.inactive == False)  # noqa: E712
    )

    # Apply access filtering unless user has CASES.ALL_CASES
    if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
        # EXISTS subquery: direct user-case assignment
        direct_exists = exists(
            select(1).where(and_(AppUserCase.app_user_id == current_user.id, AppUserCase.case_id == Case.id))
        )

        # EXISTS subquery: team membership path person -> person_team -> team_case
        team_exists = exists(
            select(1)
            .select_from(Person)
            .join(PersonTeam, PersonTeam.person_id == Person.id)
            .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
            .where(and_(Person.app_user_id == current_user.id, TeamCase.case_id == Case.id))
        )

        q = q.where(or_(direct_exists, team_exists))

    q = q.order_by(asc(Subject.last_name), asc(Subject.first_name))

    rows = (await db.execute(q)).all()

    items = []
    for case_id, case_number, subject_id, first, last, has_pic in rows:
        items.append({
            "id": encode_id("case", int(case_id)),
            "raw_db_id": int(case_id),
            "name": f"{first} {last}".strip(),
            "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(subject_id))}?s=xs" if has_pic else "/images/pfp-generic.png",
            "case_number": case_number,
        })

    return items


@router.get("/by-number/{case_number}", summary="Get case header by case number")
async def get_case_by_number(
    case_number: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Locate the case by its public number
    res = await db.execute(select(Case).where(Case.case_number == case_number))
    case_row = res.scalar_one_or_none()
    if case_row is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Access control
    if not await can_user_access_case(db, current_user.id, int(case_row.id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Fetch joins: subject, demographics, circumstances, management, disposition + ref codes
    SexRV = aliased(RefValue)
    RaceRV = aliased(RefValue)
    CsecRV = aliased(RefValue)
    MstatRV = aliased(RefValue)
    MclassRV = aliased(RefValue)
    ReqByRV = aliased(RefValue)
    # Disposition ref aliases
    ScopeRV = aliased(RefValue)
    ClassRV = aliased(RefValue)
    StatusRV = aliased(RefValue)
    LivingRV = aliased(RefValue)
    FoundByRV = aliased(RefValue)

    q = (
        select(
            Case.id.label("case_id"),
            Case.case_number,
            Case.date_intake,
            Case.inactive,
            Subject.id.label("subject_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.middle_name,
            Subject.nicknames,
            Subject.profile_pic.isnot(None).label("has_pic"),
            CaseDemographics.age_when_missing,
            CaseDemographics.date_of_birth,
            CaseDemographics.height,
            CaseDemographics.weight,
            CaseDemographics.hair_color,
            CaseDemographics.hair_length,
            CaseDemographics.eye_color,
            CaseDemographics.identifying_marks,
            CaseDemographics.sex_id,
            CaseDemographics.race_id,
            SexRV.code.label("sex_code"),
            RaceRV.code.label("race_code"),
            CaseCircumstances.date_missing,
            CaseManagement.consent_sent,
            CaseManagement.consent_returned,
            CaseManagement.flyer_complete,
            CaseManagement.ottic,
            CaseManagement.csec_id,
            CaseManagement.missing_status_id,
            CaseManagement.classification_id,
            CaseManagement.requested_by_id,
            CsecRV.code.label("csec_code"),
            MstatRV.code.label("missing_status_code"),
            MclassRV.code.label("classification_code"),
            ReqByRV.code.label("requested_by_code"),
            CaseManagement.ncic_case_number,
            CaseManagement.ncmec_case_number,
            CaseManagement.le_case_number,
            CaseManagement.le_24hour_contact,
            CaseManagement.ss_case_number,
            CaseManagement.ss_24hour_contact,
            CaseManagement.jpo_case_number,
            CaseManagement.jpo_24hour_contact,
            CasePatternOfLife.school,
            CasePatternOfLife.grade,
            CasePatternOfLife.missing_classes,
            CasePatternOfLife.school_laptop,
            CasePatternOfLife.school_laptop_taken,
            CasePatternOfLife.school_address,
            CasePatternOfLife.employed,
            CasePatternOfLife.employer,
            CasePatternOfLife.work_hours,
            CasePatternOfLife.employer_address,
            CasePatternOfLife.confidants,
            # Disposition
            CaseDisposition.shepherds_contributed_intel,
            CaseDisposition.date_found,
            CaseDisposition.scope_id,
            CaseDisposition.class_id,
            CaseDisposition.status_id,
            CaseDisposition.living_id,
            CaseDisposition.found_by_id,
            ScopeRV.code.label("scope_code"),
            ClassRV.code.label("class_code"),
            StatusRV.code.label("status_code"),
            LivingRV.code.label("living_code"),
            FoundByRV.code.label("found_by_code"),
        )
        .join(Subject, Subject.id == Case.subject_id)
        .join(CaseDemographics, CaseDemographics.case_id == Case.id, isouter=True)
        .join(SexRV, SexRV.id == CaseDemographics.sex_id, isouter=True)
        .join(RaceRV, RaceRV.id == CaseDemographics.race_id, isouter=True)
        .join(CaseCircumstances, CaseCircumstances.case_id == Case.id, isouter=True)
        .join(CaseManagement, CaseManagement.case_id == Case.id, isouter=True)
        .join(CsecRV, CsecRV.id == CaseManagement.csec_id, isouter=True)
        .join(MstatRV, MstatRV.id == CaseManagement.missing_status_id, isouter=True)
        .join(MclassRV, MclassRV.id == CaseManagement.classification_id, isouter=True)
        .join(ReqByRV, ReqByRV.id == CaseManagement.requested_by_id, isouter=True)
        .join(CasePatternOfLife, CasePatternOfLife.case_id == Case.id, isouter=True)
        .join(CaseDisposition, CaseDisposition.case_id == Case.id, isouter=True)
        .join(ScopeRV, ScopeRV.id == CaseDisposition.scope_id, isouter=True)
        .join(ClassRV, ClassRV.id == CaseDisposition.class_id, isouter=True)
        .join(StatusRV, StatusRV.id == CaseDisposition.status_id, isouter=True)
        .join(LivingRV, LivingRV.id == CaseDisposition.living_id, isouter=True)
        .join(FoundByRV, FoundByRV.id == CaseDisposition.found_by_id, isouter=True)
        .where(Case.id == case_row.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    (
        case_id,
        case_number_val,
        date_intake,
        inactive,
        subject_id,
        first,
        last,
        middle,
        nicknames,
        has_pic,
        age_when_missing,
        date_of_birth,
        height,
        weight,
        hair_color,
        hair_length,
        eye_color,
        identifying_marks,
        sex_id,
        race_id,
        sex_code,
        race_code,
        date_missing,
        consent_sent,
        consent_returned,
        flyer_complete,
        ottic,
        csec_id,
        missing_status_id,
        classification_id,
        mgmt_requested_by_id,
        csec_code,
        missing_status_code,
        classification_code,
        mgmt_requested_by_code,
        ncic_case_number,
        ncmec_case_number,
        le_case_number,
        le_24hour_contact,
        ss_case_number,
        ss_24hour_contact,
        jpo_case_number,
        jpo_24hour_contact,
        pol_school,
        pol_grade,
        pol_missing_classes,
        pol_school_laptop,
        pol_school_laptop_taken,
        pol_school_address,
        pol_employed,
        pol_employer,
        pol_work_hours,
        pol_employer_address,
        pol_confidants,
        disp_shep_intel,
        disp_date_found,
        disp_scope_id,
        disp_class_id,
        disp_status_id,
        disp_living_id,
        disp_found_by_id,
        disp_scope_code,
        disp_class_code,
        disp_status_code,
        disp_living_code,
        disp_found_by_code,
    ) = row

    subject_opaque = encode_id("subject", int(subject_id))
    case_opaque = encode_id("case", int(case_id))

    return {
        "case": {
            "id": case_opaque,
            "raw_db_id": int(case_id),
            "case_number": case_number_val,
            "date_intake": date_intake.isoformat() if date_intake is not None else None,
            "inactive": bool(inactive) if inactive is not None else False,
            "subject_id": subject_opaque,
        },
        "subject": {
            "id": subject_opaque,
            "first_name": first,
            "last_name": last,
            "middle_name": middle,
            "nicknames": nicknames,
            "has_pic": bool(has_pic),
            "photo_url": f"/api/v1/media/pfp/subject/{subject_opaque}?s=sm" if has_pic else "/images/pfp-generic.png",
        },
        "demographics": {
            "age_when_missing": int(age_when_missing) if age_when_missing is not None else None,
            "date_of_birth": date_of_birth.isoformat() if date_of_birth is not None else None,
            "height": height,
            "weight": weight,
            "hair_color": hair_color,
            "hair_length": hair_length,
            "eye_color": eye_color,
            "identifying_marks": identifying_marks,
            "sex_id": int(sex_id) if sex_id is not None else None,
            "race_id": int(race_id) if race_id is not None else None,
            "sex_code": sex_code,
            "race_code": race_code,
        },
        "circumstances": {
            "date_missing": date_missing.isoformat() if date_missing is not None else None,
        },
        "management": {
            "consent_sent": bool(consent_sent) if consent_sent is not None else False,
            "consent_returned": bool(consent_returned) if consent_returned is not None else False,
            "flyer_complete": bool(flyer_complete) if flyer_complete is not None else False,
            "ottic": bool(ottic) if ottic is not None else False,
            "csec_id": int(csec_id) if csec_id is not None else None,
            "missing_status_id": int(missing_status_id) if missing_status_id is not None else None,
            "classification_id": int(classification_id) if classification_id is not None else None,
            "requested_by_id": int(mgmt_requested_by_id) if mgmt_requested_by_id is not None else None,
            "csec_code": csec_code,
            "missing_status_code": missing_status_code,
            "classification_code": classification_code,
            "requested_by_code": mgmt_requested_by_code,
            "ncic_case_number": ncic_case_number,
            "ncmec_case_number": ncmec_case_number,
            "le_case_number": le_case_number,
            "le_24hour_contact": le_24hour_contact,
            "ss_case_number": ss_case_number,
            "ss_24hour_contact": ss_24hour_contact,
            "jpo_case_number": jpo_case_number,
            "jpo_24hour_contact": jpo_24hour_contact,
        },
        "pattern_of_life": {
            "school": pol_school,
            "grade": pol_grade,
            "missing_classes": bool(pol_missing_classes) if pol_missing_classes is not None else False,
            "school_laptop": bool(pol_school_laptop) if pol_school_laptop is not None else False,
            "school_laptop_taken": bool(pol_school_laptop_taken) if pol_school_laptop_taken is not None else False,
            "school_address": pol_school_address,
            "employed": bool(pol_employed) if pol_employed is not None else False,
            "employer": pol_employer,
            "work_hours": pol_work_hours,
            "employer_address": pol_employer_address,
            "confidants": pol_confidants,
        },
        "disposition": {
            "shepherds_contributed_intel": bool(disp_shep_intel) if disp_shep_intel is not None else False,
            "date_found": disp_date_found.isoformat() if disp_date_found is not None else None,
            "scope_id": int(disp_scope_id) if disp_scope_id is not None else None,
            "class_id": int(disp_class_id) if disp_class_id is not None else None,
            "status_id": int(disp_status_id) if disp_status_id is not None else None,
            "living_id": int(disp_living_id) if disp_living_id is not None else None,
            "found_by_id": int(disp_found_by_id) if disp_found_by_id is not None else None,
            "scope_code": disp_scope_code,
            "class_code": disp_class_code,
            "status_code": disp_status_code,
            "living_code": disp_living_code,
            "found_by_code": disp_found_by_code,
        }
    }



@router.put("/{case_id}/demographics", summary="Upsert case demographics")
async def upsert_case_demographics(
    case_id: str,
    payload: CaseDemographicsUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Find existing demographics row for case
    res = await db.execute(select(CaseDemographics).where(CaseDemographics.case_id == int(case_db_id)))
    row = res.scalar_one_or_none()

    # Decode optional ref ids (opaque -> int)
    def _dec(model: str, oid: Optional[str]):
        if not oid:
            return None
        try:
            return decode_id(model, oid)
        except Exception:
            return None

    updates = {
        "date_of_birth": payload.date_of_birth,
        "age_when_missing": payload.age_when_missing,
        "height": payload.height,
        "weight": payload.weight,
        "hair_color": payload.hair_color,
        "hair_length": payload.hair_length,
        "eye_color": payload.eye_color,
        "identifying_marks": payload.identifying_marks,
        "sex_id": _dec("ref_value", payload.sex_id) if payload.sex_id is not None else None,
        "race_id": _dec("ref_value", payload.race_id) if payload.race_id is not None else None,
    }

    if row is None:
        row = CaseDemographics(case_id=int(case_db_id), **updates)
        db.add(row)
    else:
        for k, v in updates.items():
            setattr(row, k, v)

    await db.commit()
    return {"ok": True}


@router.put("/{case_id}/pattern-of-life", summary="Upsert case pattern of life")
async def upsert_case_pattern_of_life(
    case_id: str,
    payload: CasePatternOfLifeUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Find existing or create new
    res = await db.execute(select(CasePatternOfLife).where(CasePatternOfLife.case_id == int(case_db_id)))
    row = res.scalar_one_or_none()

    updates = {
        "school": payload.school,
        "grade": payload.grade,
        "missing_classes": bool(payload.missing_classes) if payload.missing_classes is not None else False,
        "school_laptop": bool(payload.school_laptop) if payload.school_laptop is not None else False,
        "school_laptop_taken": bool(payload.school_laptop_taken) if payload.school_laptop_taken is not None else False,
        "school_address": payload.school_address,
        "employed": bool(payload.employed) if payload.employed is not None else False,
        "employer": payload.employer,
        "work_hours": payload.work_hours,
        "employer_address": payload.employer_address,
        "confidants": payload.confidants,
    }

    if row is None:
        row = CasePatternOfLife(case_id=int(case_db_id), **updates)
        db.add(row)
    else:
        for k, v in updates.items():
            setattr(row, k, v)

    await db.commit()
    return {"ok": True}


@router.get("/{case_id}/exploitation", summary="List selected exploitation refs for a case")
async def get_case_exploitation(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    rows = (
        await db.execute(
            select(CaseExploitation.exploitation_id, RefValue.code)
            .join(RefValue, RefValue.id == CaseExploitation.exploitation_id)
            .where(CaseExploitation.case_id == int(case_db_id))
        )
    ).all()
    ids = [encode_id("ref_value", int(eid)) for (eid, _code) in rows]
    codes = [code for (_eid, code) in rows]
    return {"exploitation_ids": ids, "exploitation_codes": codes}


@router.put("/{case_id}/exploitation", summary="Sync case exploitation selections")
async def upsert_case_exploitation(
    case_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    raw_ids = payload.get("exploitation_ids") or []
    # decode opaque ids or accept numeric strings; ignore invalid
    dec_ids = []
    for oid in raw_ids:
        try:
            s = str(oid)
            if s.isdigit():
                dec_ids.append(int(s))
            else:
                dec_ids.append(int(decode_id("ref_value", s)))
        except Exception:
            continue
    dec_set = set(dec_ids)

    # Fetch existing
    existing_rows = (await db.execute(select(CaseExploitation).where(CaseExploitation.case_id == int(case_db_id)))).scalars().all()
    existing_ids = set([int(r.exploitation_id) for r in existing_rows])

    # Delete removed
    for r in existing_rows:
        if int(r.exploitation_id) not in dec_set:
            await db.delete(r)

    # Insert new
    to_add = dec_set - existing_ids
    for rid in to_add:
        db.add(CaseExploitation(case_id=int(case_db_id), exploitation_id=int(rid)))

    await db.commit()
    return {"ok": True}


@router.get("/victimology/catalog", summary="List victimology categories with questions")
async def get_victimology_catalog(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Categories sorted by sort_order (nulls last), then category name
    q_cat = (
        select(VictimologyCategory)
        .order_by(
            sa.case((VictimologyCategory.sort_order.is_(None), 1), else_=0).asc(),
            VictimologyCategory.sort_order.asc(),
            VictimologyCategory.category.asc(),
        )
    )
    cats = (await db.execute(q_cat)).scalars().all()

    # Preload all victimology rows and bucket by category
    q_vic = (
        select(Victimology)
        .order_by(
            sa.case((Victimology.sort_order.is_(None), 1), else_=0).asc(),
            Victimology.sort_order.asc(),
            Victimology.id.asc(),
        )
    )
    vics = (await db.execute(q_vic)).scalars().all()
    by_cat = {}
    for v in vics:
        by_cat.setdefault(int(getattr(v, 'victimology_category_id')), []).append(v)

    def enc(model, val):
        return encode_id(model, int(val)) if val is not None else None

    items = []
    for c in cats:
        items.append({
            "id": enc("victimology_category", c.id),
            "category": c.category,
            "sort_order": int(c.sort_order) if c.sort_order is not None else None,
            "questions": [
                {
                    "id": enc("victimology", v.id),
                    "db_id": int(v.id),
                    "question": v.question,
                    "follow_up": getattr(v, "follow_up", None),
                    "sort_order": int(v.sort_order) if v.sort_order is not None else None,
                }
                for v in by_cat.get(int(c.id), [])
            ]
        })

    return items


@router.get("/{case_id}/victimology", summary="List case victimology answers")
async def get_case_victimology(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    rows = (
        await db.execute(
            select(CaseVictimology).where(CaseVictimology.case_id == int(case_db_id))
        )
    ).scalars().all()

    def enc(model, val):
        return encode_id(model, int(val)) if val is not None else None

    # Return a normalized list
    return [
        {
            "id": enc("case_victimology", r.id),
            "victimology_id": enc("victimology", r.victimology_id),
            "victimology_db_id": int(r.victimology_id) if getattr(r, 'victimology_id', None) is not None else None,
            "answer_id": enc("ref_value", r.answer_id) if r.answer_id is not None else None,
            "details": r.details,
        }
        for r in rows
    ]


class CaseVictimologyUpsertPayload(BaseModel):
    answer_id: Optional[str] = None
    details: Optional[str] = None


@router.put("/{case_id}/victimology/{victimology_id}", summary="Upsert case victimology answer")
async def upsert_case_victimology(
    case_id: str,
    victimology_id: str,
    payload: CaseVictimologyUpsertPayload = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        vic_db_id = decode_id("victimology", victimology_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Question not found")

    # Decode optional ref_value id
    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s))
        except Exception:
            return None

    # Find existing
    row = (
        await db.execute(
            select(CaseVictimology).where(
                CaseVictimology.case_id == int(case_db_id),
                CaseVictimology.victimology_id == int(vic_db_id),
            )
        )
    ).scalar_one_or_none()

    if row is None:
        row = CaseVictimology(
            case_id=int(case_db_id),
            victimology_id=int(vic_db_id),
            answer_id=_dec_ref(getattr(payload, "answer_id", None)),
            details=getattr(payload, "details", None),
        )
        db.add(row)
    else:
        if hasattr(payload, "answer_id"):
            row.answer_id = _dec_ref(payload.answer_id)
        if hasattr(payload, "details"):
            row.details = payload.details

    await db.commit()
    return {"ok": True}


@router.get("/{case_id}/circumstances", summary="Get case circumstances")
async def get_case_circumstances(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    row = (await db.execute(select(CaseCircumstances).where(CaseCircumstances.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        return {}

    def enc_ref(v):
        return encode_id("ref_value", int(v)) if v is not None else None

    return {
        "id": encode_id("case_circumstances", int(row.id)) if getattr(row, 'id', None) is not None else None,
        "case_id": encode_id("case", int(row.case_id)),
        "date_missing": getattr(row, 'date_missing', None).isoformat() if getattr(row, 'date_missing', None) is not None else None,
        "time_missing": getattr(row, 'time_missing', None).isoformat() if getattr(row, 'time_missing', None) is not None else None,
        "date_reported": getattr(row, 'date_reported', None).isoformat() if getattr(row, 'date_reported', None) is not None else None,
        "address": getattr(row, 'address', None),
        "city": getattr(row, 'city', None),
        "state_id": enc_ref(getattr(row, 'state_id', None)),
        "point_last_seen": getattr(row, 'point_last_seen', None),
        "have_id_id": enc_ref(getattr(row, 'have_id_id', None)),
        "id_taken_id": enc_ref(getattr(row, 'id_taken_id', None)),
        "have_money_id": enc_ref(getattr(row, 'have_money_id', None)),
        "money_taken_id": enc_ref(getattr(row, 'money_taken_id', None)),
        "have_cc_id": enc_ref(getattr(row, 'have_cc_id', None)),
        "cc_taken_id": enc_ref(getattr(row, 'cc_taken_id', None)),
        "vehicle_taken": bool(getattr(row, 'vehicle_taken', False)),
        "vehicle_desc": getattr(row, 'vehicle_desc', None),
        "with_whom": getattr(row, 'with_whom', None),
        "what_happened": getattr(row, 'what_happened', None),
        "clothing_top": getattr(row, 'clothing_top', None),
        "clothing_bottom": getattr(row, 'clothing_bottom', None),
        "clothing_shoes": getattr(row, 'clothing_shoes', None),
        "clothing_outerwear": getattr(row, 'clothing_outerwear', None),
        "clothing_innerwear": getattr(row, 'clothing_innerwear', None),
        "bags": getattr(row, 'bags', None),
        "other_items": getattr(row, 'other_items', None),
        "devices": getattr(row, 'devices', None),
        "mobile_carrier_id": enc_ref(getattr(row, 'mobile_carrier_id', None)),
        "mobile_carrier_other": getattr(row, 'mobile_carrier_other', None),
        "voip_id": enc_ref(getattr(row, 'voip_id', None)),
        "wifi_only": bool(getattr(row, 'wifi_only', False)),
    }


@router.get("/{case_id}/search-urgency", summary="Get case search urgency")
async def get_case_search_urgency(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    row = (
        await db.execute(select(CaseSearchUrgency).where(CaseSearchUrgency.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if row is None:
        return {}

    def enc_ref(v):
        return encode_id("ref_value", int(v)) if v is not None else None

    return {
        "id": encode_id("case_search_urgency", int(row.id)) if getattr(row, 'id', None) is not None else None,
        "case_id": encode_id("case", int(row.case_id)),
        "age_id": enc_ref(getattr(row, 'age_id', None)),
        "physical_condition_id": enc_ref(getattr(row, 'physical_condition_id', None)),
        "medical_condition_id": enc_ref(getattr(row, 'medical_condition_id', None)),
        "personal_risk_id": enc_ref(getattr(row, 'personal_risk_id', None)),
        "online_risk_id": enc_ref(getattr(row, 'online_risk_id', None)),
        "family_risk_id": enc_ref(getattr(row, 'family_risk_id', None)),
        "behavioral_risk_id": enc_ref(getattr(row, 'behavioral_risk_id', None)),
        "score": int(getattr(row, 'score', 0)) if getattr(row, 'score', None) is not None else None,
    }


@router.put("/{case_id}/search-urgency", summary="Upsert case search urgency")
async def upsert_case_search_urgency(
    case_id: str,
    payload: CaseSearchUrgencyUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Find existing or create new
    res = await db.execute(select(CaseSearchUrgency).where(CaseSearchUrgency.case_id == int(case_db_id)))
    row = res.scalar_one_or_none()

    def _dec_ref(oid):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    updates = {
        "age_id": _dec_ref(getattr(payload, 'age_id', None)) if hasattr(payload, 'age_id') else None,
        "physical_condition_id": _dec_ref(getattr(payload, 'physical_condition_id', None)) if hasattr(payload, 'physical_condition_id') else None,
        "medical_condition_id": _dec_ref(getattr(payload, 'medical_condition_id', None)) if hasattr(payload, 'medical_condition_id') else None,
        "personal_risk_id": _dec_ref(getattr(payload, 'personal_risk_id', None)) if hasattr(payload, 'personal_risk_id') else None,
        "online_risk_id": _dec_ref(getattr(payload, 'online_risk_id', None)) if hasattr(payload, 'online_risk_id') else None,
        "family_risk_id": _dec_ref(getattr(payload, 'family_risk_id', None)) if hasattr(payload, 'family_risk_id') else None,
        "behavioral_risk_id": _dec_ref(getattr(payload, 'behavioral_risk_id', None)) if hasattr(payload, 'behavioral_risk_id') else None,
    }

    if row is None:
        row = CaseSearchUrgency(case_id=int(case_db_id), **updates)
        db.add(row)
    else:
        for k, v in updates.items():
            # Only set attribute if present in payload (allows partial updates)
            if hasattr(payload, k):
                setattr(row, k, v)

    # Compute score if all seven selections present
    sel_ids = [
        getattr(row, 'age_id', None),
        getattr(row, 'physical_condition_id', None),
        getattr(row, 'medical_condition_id', None),
        getattr(row, 'personal_risk_id', None),
        getattr(row, 'online_risk_id', None),
        getattr(row, 'family_risk_id', None),
        getattr(row, 'behavioral_risk_id', None),
    ]

    score_val = None
    if all(v is not None for v in sel_ids):
        # Sum sort_order values for selected ref_values
        vals = (
            await db.execute(
                select(RefValue.id, RefValue.sort_order).where(RefValue.id.in_([int(v) for v in sel_ids]))
            )
        ).all()
        by_id = {int(i): (int(s) if s is not None else 0) for i, s in vals}
        score_val = sum(by_id.get(int(v), 0) for v in sel_ids)
        row.score = int(score_val)
    else:
        row.score = None

    await db.commit()
    return {"ok": True, "score": score_val}


@router.put("/{case_id}/circumstances", summary="Upsert case circumstances")
async def upsert_case_circumstances(
    case_id: str,
    payload: CaseCircumstancesUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Find existing or create new
    res = await db.execute(select(CaseCircumstances).where(CaseCircumstances.case_id == int(case_db_id)))
    row = res.scalar_one_or_none()

    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    updates = {
        "date_missing": getattr(payload, 'date_missing', None),
        "time_missing": getattr(payload, 'time_missing', None),
        "date_reported": getattr(payload, 'date_reported', None),
        "address": getattr(payload, 'address', None),
        "city": getattr(payload, 'city', None),
        "state_id": _dec_ref(getattr(payload, 'state_id', None)) if hasattr(payload, 'state_id') else None,
        "point_last_seen": getattr(payload, 'point_last_seen', None),
        "have_id_id": _dec_ref(getattr(payload, 'have_id_id', None)) if hasattr(payload, 'have_id_id') else None,
        "id_taken_id": _dec_ref(getattr(payload, 'id_taken_id', None)) if hasattr(payload, 'id_taken_id') else None,
        "have_money_id": _dec_ref(getattr(payload, 'have_money_id', None)) if hasattr(payload, 'have_money_id') else None,
        "money_taken_id": _dec_ref(getattr(payload, 'money_taken_id', None)) if hasattr(payload, 'money_taken_id') else None,
        "have_cc_id": _dec_ref(getattr(payload, 'have_cc_id', None)) if hasattr(payload, 'have_cc_id') else None,
        "cc_taken_id": _dec_ref(getattr(payload, 'cc_taken_id', None)) if hasattr(payload, 'cc_taken_id') else None,
        "vehicle_taken": bool(getattr(payload, 'vehicle_taken', False)),
        "vehicle_desc": getattr(payload, 'vehicle_desc', None),
        "with_whom": getattr(payload, 'with_whom', None),
        "what_happened": getattr(payload, 'what_happened', None),
        "clothing_top": getattr(payload, 'clothing_top', None),
        "clothing_bottom": getattr(payload, 'clothing_bottom', None),
        "clothing_shoes": getattr(payload, 'clothing_shoes', None),
        "clothing_outerwear": getattr(payload, 'clothing_outerwear', None),
        "clothing_innerwear": getattr(payload, 'clothing_innerwear', None),
        "bags": getattr(payload, 'bags', None),
        "other_items": getattr(payload, 'other_items', None),
        "devices": getattr(payload, 'devices', None),
        "mobile_carrier_id": _dec_ref(getattr(payload, 'mobile_carrier_id', None)) if hasattr(payload, 'mobile_carrier_id') else None,
        "mobile_carrier_other": getattr(payload, 'mobile_carrier_other', None),
        "voip_id": _dec_ref(getattr(payload, 'voip_id', None)) if hasattr(payload, 'voip_id') else None,
        "wifi_only": bool(getattr(payload, 'wifi_only', False)),
    }

    if row is None:
        row = CaseCircumstances(case_id=int(case_db_id), **updates)
        db.add(row)
    else:
        for k, v in updates.items():
            setattr(row, k, v)

    await db.commit()
    return {"ok": True}


@router.put("/{case_id}/management", summary="Upsert case management")
async def upsert_case_management(
    case_id: str,
    payload: CaseManagementUpsert = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Find existing or create new
    res = await db.execute(select(CaseManagement).where(CaseManagement.case_id == int(case_db_id)))
    row = res.scalar_one_or_none()

    def _dec(oid: Optional[str]):
        if not oid:
            return None
        try:
            return decode_id("ref_value", oid)
        except Exception:
            return None

    updates = {
        "consent_sent": bool(payload.consent_sent) if payload.consent_sent is not None else False,
        "consent_returned": bool(payload.consent_returned) if payload.consent_returned is not None else False,
        "flyer_complete": bool(payload.flyer_complete) if payload.flyer_complete is not None else False,
        "ottic": bool(payload.ottic) if payload.ottic is not None else False,
        "csec_id": _dec(payload.csec_id) if payload.csec_id is not None else None,
        "missing_status_id": _dec(payload.missing_status_id) if payload.missing_status_id is not None else None,
        "classification_id": _dec(payload.classification_id) if payload.classification_id is not None else None,
        "requested_by_id": _dec(payload.requested_by_id) if getattr(payload, 'requested_by_id', None) is not None else None,
        "ncic_case_number": payload.ncic_case_number,
        "ncmec_case_number": payload.ncmec_case_number,
        "le_case_number": payload.le_case_number,
        "le_24hour_contact": payload.le_24hour_contact,
        "ss_case_number": payload.ss_case_number,
        "ss_24hour_contact": payload.ss_24hour_contact,
        "jpo_case_number": payload.jpo_case_number,
        "jpo_24hour_contact": payload.jpo_24hour_contact,
    }

    if row is None:
        row = CaseManagement(case_id=int(case_db_id), **updates)
        db.add(row)
    else:
        for k, v in updates.items():
            setattr(row, k, v)

    await db.commit()
    return {"ok": True}





# -------- Social Media (moved to social_media.py) --------


# -------- Timeline moved to timeline.py --------


# -------- Intel Activity moved to activity.py --------











@router.get("/{case_id}/by-id", summary="Get case header by case id")
async def get_case_by_id(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Returns the same composite structure as GET /cases/by-number/{case_number},
    but addressed by encrypted case id. Read-only.
    """
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Aliases for ref tables (mirrors get_case_by_number)
    SexRV = aliased(RefValue)
    RaceRV = aliased(RefValue)
    CsecRV = aliased(RefValue)
    MstatRV = aliased(RefValue)
    MclassRV = aliased(RefValue)
    ReqByRV = aliased(RefValue)
    ScopeRV = aliased(RefValue)
    ClassRV = aliased(RefValue)
    StatusRV = aliased(RefValue)
    LivingRV = aliased(RefValue)
    FoundByRV = aliased(RefValue)

    q = (
        select(
            Case.id.label("case_id"),
            Case.case_number,
            Case.date_intake,
            Case.inactive,
            Subject.id.label("subject_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.middle_name,
            Subject.nicknames,
            Subject.profile_pic.isnot(None).label("has_pic"),
            CaseDemographics.age_when_missing,
            CaseDemographics.date_of_birth,
            CaseDemographics.height,
            CaseDemographics.weight,
            CaseDemographics.hair_color,
            CaseDemographics.hair_length,
            CaseDemographics.eye_color,
            CaseDemographics.identifying_marks,
            CaseDemographics.sex_id,
            CaseDemographics.race_id,
            SexRV.code.label("sex_code"),
            RaceRV.code.label("race_code"),
            CaseCircumstances.date_missing,
            CaseManagement.consent_sent,
            CaseManagement.consent_returned,
            CaseManagement.flyer_complete,
            CaseManagement.ottic,
            CaseManagement.csec_id,
            CaseManagement.missing_status_id,
            CaseManagement.classification_id,
            CaseManagement.requested_by_id,
            CsecRV.code.label("csec_code"),
            MstatRV.code.label("missing_status_code"),
            MclassRV.code.label("classification_code"),
            ReqByRV.code.label("requested_by_code"),
            CaseManagement.ncic_case_number,
            CaseManagement.ncmec_case_number,
            CaseManagement.le_case_number,
            CaseManagement.le_24hour_contact,
            CaseManagement.ss_case_number,
            CaseManagement.ss_24hour_contact,
            CaseManagement.jpo_case_number,
            CaseManagement.jpo_24hour_contact,
            CasePatternOfLife.school,
            CasePatternOfLife.grade,
            CasePatternOfLife.missing_classes,
            CasePatternOfLife.school_laptop,
            CasePatternOfLife.school_laptop_taken,
            CasePatternOfLife.school_address,
            CasePatternOfLife.employed,
            CasePatternOfLife.employer,
            CasePatternOfLife.work_hours,
            CasePatternOfLife.employer_address,
            CasePatternOfLife.confidants,
            CaseDisposition.shepherds_contributed_intel,
            CaseDisposition.date_found,
            CaseDisposition.scope_id,
            CaseDisposition.class_id,
            CaseDisposition.status_id,
            CaseDisposition.living_id,
            CaseDisposition.found_by_id,
            ScopeRV.code.label("scope_code"),
            ClassRV.code.label("class_code"),
            StatusRV.code.label("status_code"),
            LivingRV.code.label("living_code"),
            FoundByRV.code.label("found_by_code"),
        )
        .join(Subject, Subject.id == Case.subject_id)
        .join(CaseDemographics, CaseDemographics.case_id == Case.id, isouter=True)
        .join(SexRV, SexRV.id == CaseDemographics.sex_id, isouter=True)
        .join(RaceRV, RaceRV.id == CaseDemographics.race_id, isouter=True)
        .join(CaseCircumstances, CaseCircumstances.case_id == Case.id, isouter=True)
        .join(CaseManagement, CaseManagement.case_id == Case.id, isouter=True)
        .join(CsecRV, CsecRV.id == CaseManagement.csec_id, isouter=True)
        .join(MstatRV, MstatRV.id == CaseManagement.missing_status_id, isouter=True)
        .join(MclassRV, MclassRV.id == CaseManagement.classification_id, isouter=True)
        .join(ReqByRV, ReqByRV.id == CaseManagement.requested_by_id, isouter=True)
        .join(CasePatternOfLife, CasePatternOfLife.case_id == Case.id, isouter=True)
        .join(CaseDisposition, CaseDisposition.case_id == Case.id, isouter=True)
        .join(ScopeRV, ScopeRV.id == CaseDisposition.scope_id, isouter=True)
        .join(ClassRV, ClassRV.id == CaseDisposition.class_id, isouter=True)
        .join(StatusRV, StatusRV.id == CaseDisposition.status_id, isouter=True)
        .join(LivingRV, LivingRV.id == CaseDisposition.living_id, isouter=True)
        .join(FoundByRV, FoundByRV.id == CaseDisposition.found_by_id, isouter=True)
        .where(Case.id == int(case_db_id))
    )

    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    (
        case_id_val,
        case_number_val,
        date_intake,
        inactive,
        subject_id,
        first,
        last,
        middle,
        nicknames,
        has_pic,
        age_when_missing,
        date_of_birth,
        height,
        weight,
        hair_color,
        hair_length,
        eye_color,
        identifying_marks,
        sex_id,
        race_id,
        sex_code,
        race_code,
        date_missing,
        consent_sent,
        consent_returned,
        flyer_complete,
        ottic,
        csec_id,
        missing_status_id,
        classification_id,
        mgmt_requested_by_id,
        csec_code,
        missing_status_code,
        classification_code,
        mgmt_requested_by_code,
        ncic_case_number,
        ncmec_case_number,
        le_case_number,
        le_24hour_contact,
        ss_case_number,
        ss_24hour_contact,
        jpo_case_number,
        jpo_24hour_contact,
        pol_school,
        pol_grade,
        pol_missing_classes,
        pol_school_laptop,
        pol_school_laptop_taken,
        pol_school_address,
        pol_employed,
        pol_employer,
        pol_work_hours,
        pol_employer_address,
        pol_confidants,
        disp_shep_intel,
        disp_date_found,
        disp_scope_id,
        disp_class_id,
        disp_status_id,
        disp_living_id,
        disp_found_by_id,
        disp_scope_code,
        disp_class_code,
        disp_status_code,
        disp_living_code,
        disp_found_by_code,
    ) = row

    subject_opaque = encode_id("subject", int(subject_id))
    case_opaque = encode_id("case", int(case_id_val))

    return {
        "case": {
            "id": case_opaque,
            "raw_db_id": int(case_id_val),
            "case_number": case_number_val,
            "date_intake": date_intake.isoformat() if date_intake is not None else None,
            "inactive": bool(inactive) if inactive is not None else False,
            "subject_id": subject_opaque,
        },
        "subject": {
            "id": subject_opaque,
            "first_name": first,
            "last_name": last,
            "middle_name": middle,
            "nicknames": nicknames,
            "has_pic": bool(has_pic),
            "photo_url": f"/api/v1/media/pfp/subject/{subject_opaque}?s=sm" if has_pic else "/images/pfp-generic.png",
        },
        "demographics": {
            "age_when_missing": int(age_when_missing) if age_when_missing is not None else None,
            "date_of_birth": date_of_birth.isoformat() if date_of_birth is not None else None,
            "height": height,
            "weight": weight,
            "hair_color": hair_color,
            "hair_length": hair_length,
            "eye_color": eye_color,
            "identifying_marks": identifying_marks,
            "sex_id": int(sex_id) if sex_id is not None else None,
            "race_id": int(race_id) if race_id is not None else None,
            "sex_code": sex_code,
            "race_code": race_code,
        },
        "circumstances": {
            "date_missing": date_missing.isoformat() if date_missing is not None else None,
        },
        "management": {
            "consent_sent": bool(consent_sent) if consent_sent is not None else False,
            "consent_returned": bool(consent_returned) if consent_returned is not None else False,
            "flyer_complete": bool(flyer_complete) if flyer_complete is not None else False,
            "ottic": bool(ottic) if ottic is not None else False,
            "csec_id": int(csec_id) if csec_id is not None else None,
            "missing_status_id": int(missing_status_id) if missing_status_id is not None else None,
            "classification_id": int(classification_id) if classification_id is not None else None,
            "requested_by_id": int(mgmt_requested_by_id) if mgmt_requested_by_id is not None else None,
            "csec_code": csec_code,
            "missing_status_code": missing_status_code,
            "classification_code": classification_code,
            "requested_by_code": mgmt_requested_by_code,
            "ncic_case_number": ncic_case_number,
            "ncmec_case_number": ncmec_case_number,
            "le_case_number": le_case_number,
            "le_24hour_contact": le_24hour_contact,
            "ss_case_number": ss_case_number,
            "ss_24hour_contact": ss_24hour_contact,
            "jpo_case_number": jpo_case_number,
            "jpo_24hour_contact": jpo_24hour_contact,
        },
        "pattern_of_life": {
            "school": pol_school,
            "grade": pol_grade,
            "missing_classes": bool(pol_missing_classes) if pol_missing_classes is not None else False,
            "school_laptop": bool(pol_school_laptop) if pol_school_laptop is not None else False,
            "school_laptop_taken": bool(pol_school_laptop_taken) if pol_school_laptop_taken is not None else False,
            "school_address": pol_school_address,
            "employed": bool(pol_employed) if pol_employed is not None else False,
            "employer": pol_employer,
            "work_hours": pol_work_hours,
            "employer_address": pol_employer_address,
            "confidants": pol_confidants,
        },
        "disposition": {
            "shepherds_contributed_intel": bool(disp_shep_intel) if disp_shep_intel is not None else False,
            "date_found": disp_date_found.isoformat() if disp_date_found is not None else None,
            "scope_id": int(disp_scope_id) if disp_scope_id is not None else None,
            "class_id": int(disp_class_id) if disp_class_id is not None else None,
            "status_id": int(disp_status_id) if disp_status_id is not None else None,
            "living_id": int(disp_living_id) if disp_living_id is not None else None,
            "found_by_id": int(disp_found_by_id) if disp_found_by_id is not None else None,
            "scope_code": disp_scope_code,
            "class_code": disp_class_code,
            "status_code": disp_status_code,
            "living_code": disp_living_code,
            "found_by_code": disp_found_by_code,
        }
    }
