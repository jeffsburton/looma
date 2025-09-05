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
from app.db.models.social_media import SocialMedia
from app.db.models.ref_value import RefValue
from app.db.models.case_disposition import CaseDisposition
from app.db.models.case_exploitation import CaseExploitation
from app.db.models.case_victimology import CaseVictimology
from app.db.models.victimology import victimology as Victimology
from app.db.models.victimology_category import victimologyCategory as VictimologyCategory
from app.db.models.subject_case import SubjectCase
from app.db.models.person_case import PersonCase
from app.db.models.case_search_urgency import CaseSearchUrgency
from app.schemas.case_search_urgency import CaseSearchUrgencyUpsert
from app.schemas.case_demographics import CaseDemographicsRead, CaseDemographicsUpsert
from app.schemas.case_management import CaseManagementUpsert
from app.schemas.case_pattern_of_life import CasePatternOfLifeUpsert
from app.schemas.case_circumstances import CaseCircumstancesUpsert

# Images
from app.db.models.image import File as Image
from app.db.models.rfi import Rfi
from app.db.models.person import Person as PersonModel
from app.schemas.image import ImageRead
from app.services.s3 import get_download_link, create_file
from fastapi import UploadFile, File as UploadFileParam, Form


router = APIRouter(prefix="/cases")


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
    return team_exists


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
        csec_code,
        missing_status_code,
        classification_code,
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
        mgmt_requested_by_id,
        mgmt_requested_by_code,
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

    rows = (await db.execute(select(CaseExploitation.exploitation_id).where(CaseExploitation.case_id == int(case_db_id)))).all()
    ids = [encode_id("ref_value", int(r[0])) for r in rows]
    return {"exploitation_ids": ids}


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
    # decode opaque ids; ignore invalid
    dec_ids = []
    for oid in raw_ids:
        try:
            dec_ids.append(int(decode_id("ref_value", str(oid))))
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



@router.get("/{case_id}/subjects", summary="List investigatory subjects (subject_case rows) for a case")
async def list_case_subjects(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    RelRV = aliased(RefValue)
    q = (
        select(
            SubjectCase.id.label("sc_id"),
            SubjectCase.relationship_id,
            RelRV.name.label("relationship_name"),
            RelRV.code.label("relationship_code"),
            SubjectCase.relationship_other,
            SubjectCase.legal_guardian,
            SubjectCase.notes,
            SubjectCase.rule_out,
            Subject.id.label("subj_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.nicknames,
            Subject.phone,
            Subject.email,
            Subject.dangerous,
            Subject.danger,
        )
        .join(Subject, Subject.id == SubjectCase.subject_id)
        .join(RelRV, RelRV.id == SubjectCase.relationship_id, isouter=True)
        .where(SubjectCase.case_id == int(case_db_id))
        .order_by(asc(Subject.last_name), asc(Subject.first_name))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        sc_id,
        rel_id,
        rel_name,
        rel_code,
        rel_other,
        legal_guardian,
        notes,
        rule_out,
        subj_id,
        first,
        last,
        nicks,
        phone,
        email,
        dangerous,
        danger,
    ) in rows:
        items.append({
            "id": encode_id("subject_case", int(sc_id)),
            "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
            "relationship_name": rel_name,
            "relationship_code": rel_code,
            "relationship_other": rel_other,
            "legal_guardian": bool(legal_guardian) if legal_guardian is not None else False,
            "notes": notes,
            "rule_out": bool(rule_out) if rule_out is not None else False,
            "subject": {
                "id": encode_id("subject", int(subj_id)),
                "first_name": first,
                "last_name": last,
                "nicknames": nicks,
                "phone": phone,
                "email": email,
                "dangerous": bool(dangerous) if dangerous is not None else False,
                "danger": danger,
            },
        })

    return items


class SubjectCaseCreate(BaseModel):
    subject_id: str
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    legal_guardian: Optional[bool] = None
    notes: Optional[str] = None


@router.post(
    "/{case_id}/subjects",
    summary="Create a subject_case row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_case_subject(
    case_id: str,
    payload: SubjectCaseCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Decode subject id
    try:
        subj_db_id = decode_id("subject", payload.subject_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Ensure subject exists
    subj = (await db.execute(select(Subject.id).where(Subject.id == int(subj_db_id)))).scalar_one_or_none()
    if subj is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Prevent duplicates (UniqueConstraint also exists)
    exists_row = (await db.execute(select(SubjectCase.id).where(
        SubjectCase.case_id == int(case_db_id),
        SubjectCase.subject_id == int(subj_db_id),
    ))).scalar_one_or_none()
    if exists_row is not None:
        # Treat as idempotent
        return {"ok": True, "already_exists": True}

    # Helper to decode optional ref_value id
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

    row = SubjectCase(
        case_id=int(case_db_id),
        subject_id=int(subj_db_id),
        relationship_id=_dec_ref(payload.relationship_id) if hasattr(payload, "relationship_id") else None,
        relationship_other=getattr(payload, "relationship_other", None),
        legal_guardian=bool(getattr(payload, "legal_guardian", False)),
        notes=getattr(payload, "notes", None),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


class SubjectCasePartial(BaseModel):
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    legal_guardian: Optional[bool] = None
    notes: Optional[str] = None
    rule_out: Optional[bool] = None


@router.patch("/{case_id}/subjects/{subject_case_id}", summary="Update a subject_case row for a case")
async def update_case_subject(
    case_id: str,
    subject_case_id: str,
    payload: SubjectCasePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sc_db_id = decode_id("subject_case", subject_case_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Subject link not found")

    # Load row and ensure it belongs to the case
    row = (await db.execute(select(SubjectCase).where(SubjectCase.id == int(sc_db_id), SubjectCase.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Subject link not found")

    # Helper to decode optional ref_value id
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

    # Update only fields explicitly provided in the payload
    fields_set = getattr(payload, "model_fields_set", set())

    if "relationship_id" in fields_set:
        row.relationship_id = _dec_ref(payload.relationship_id)
    if "relationship_other" in fields_set:
        row.relationship_other = payload.relationship_other
    if "legal_guardian" in fields_set:
        row.legal_guardian = bool(payload.legal_guardian) if payload.legal_guardian is not None else False
    if "notes" in fields_set:
        row.notes = payload.notes
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}


# -------- Agency Personnel (person_case) --------
class PersonCaseCreate(BaseModel):
    person_id: str
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    notes: Optional[str] = None


@router.get("/{case_id}/persons", summary="List agency personnel (person_case rows) for a case")
async def list_case_persons(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    RelRV = aliased(RefValue)
    q = (
        select(
            PersonCase.id.label("pc_id"),
            PersonCase.relationship_id,
            RelRV.name.label("relationship_name"),
            RelRV.code.label("relationship_code"),
            PersonCase.relationship_other,
            PersonCase.notes,
            Person.id.label("person_id"),
            Person.first_name,
            Person.last_name,
            Person.phone,
            Person.email,
        )
        .join(Person, Person.id == PersonCase.person_id)
        .join(RelRV, RelRV.id == PersonCase.relationship_id, isouter=True)
        .where(PersonCase.case_id == int(case_db_id))
        .order_by(asc(Person.last_name), asc(Person.first_name))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        pc_id,
        rel_id,
        rel_name,
        rel_code,
        rel_other,
        notes,
        pid,
        first,
        last,
        phone,
        email,
    ) in rows:
        items.append({
            "id": encode_id("person_case", int(pc_id)),
            "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
            "relationship_name": rel_name,
            "relationship_code": rel_code,
            "relationship_other": rel_other,
            "notes": notes,
            "person": {
                "id": encode_id("person", int(pid)),
                "first_name": first,
                "last_name": last,
                "phone": phone,
                "email": email,
            },
        })

    return items


@router.post(
    "/{case_id}/persons",
    summary="Create a person_case row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_case_person(
    case_id: str,
    payload: PersonCaseCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        person_db_id = decode_id("person", payload.person_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Person not found")

    person_exists = (await db.execute(select(Person.id).where(Person.id == int(person_db_id)))).scalar_one_or_none()
    if person_exists is None:
        raise HTTPException(status_code=404, detail="Person not found")

    exists_row = (await db.execute(select(PersonCase.id).where(
        PersonCase.case_id == int(case_db_id),
        PersonCase.person_id == int(person_db_id),
    ))).scalar_one_or_none()
    if exists_row is not None:
        return {"ok": True, "already_exists": True}

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

    row = PersonCase(
        case_id=int(case_db_id),
        person_id=int(person_db_id),
        relationship_id=_dec_ref(payload.relationship_id) if hasattr(payload, "relationship_id") else None,
        relationship_other=getattr(payload, "relationship_other", None),
        notes=getattr(payload, "notes", None),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


class PersonCasePartial(BaseModel):
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    notes: Optional[str] = None


@router.patch("/{case_id}/persons/{person_case_id}", summary="Update a person_case row for a case")
async def update_case_person(
    case_id: str,
    person_case_id: str,
    payload: PersonCasePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        pc_db_id = decode_id("person_case", person_case_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Person link not found")

    row = (await db.execute(select(PersonCase).where(PersonCase.id == int(pc_db_id), PersonCase.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Person link not found")

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

    fields_set = getattr(payload, "model_fields_set", set())

    if "relationship_id" in fields_set:
        row.relationship_id = _dec_ref(payload.relationship_id)
    if "relationship_other" in fields_set:
        row.relationship_other = payload.relationship_other
    if "notes" in fields_set:
        row.notes = payload.notes

    await db.commit()
    return {"ok": True}


# -------- Social Media (social_media) --------
from typing import Optional as _OptionalForSM
class SocialMediaCreate(BaseModel):
    subject_id: _OptionalForSM[str] = None
    platform_id: _OptionalForSM[str] = None
    platform_other: _OptionalForSM[str] = None
    url: _OptionalForSM[str] = None
    status_id: _OptionalForSM[str] = None
    investigated_id: _OptionalForSM[str] = None
    notes: _OptionalForSM[str] = None
    rule_out: _OptionalForSM[bool] = None


@router.get("/{case_id}/social-media", summary="List social media for a case")
async def list_social_media(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    PlatRV = aliased(RefValue)
    StatRV = aliased(RefValue)
    InvRV = aliased(RefValue)
    q = (
        select(
            SocialMedia.id.label("sm_id"),
            SocialMedia.subject_id,
            SocialMedia.platform_id,
            PlatRV.name.label("platform_name"),
            PlatRV.code.label("platform_code"),
            SocialMedia.platform_other,
            SocialMedia.url,
            SocialMedia.status_id,
            StatRV.name.label("status_name"),
            StatRV.code.label("status_code"),
            SocialMedia.investigated_id,
            InvRV.name.label("investigated_name"),
            InvRV.code.label("investigated_code"),
            SocialMedia.notes,
            SocialMedia.rule_out,
            Subject.first_name,
            Subject.last_name,
        )
        .join(Subject, Subject.id == SocialMedia.subject_id, isouter=True)
        .join(PlatRV, PlatRV.id == SocialMedia.platform_id, isouter=True)
        .join(StatRV, StatRV.id == SocialMedia.status_id, isouter=True)
        .join(InvRV, InvRV.id == SocialMedia.investigated_id, isouter=True)
        .where(SocialMedia.case_id == int(case_db_id))
        .order_by(asc(Subject.last_name), asc(Subject.first_name), asc(SocialMedia.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        sm_id,
        subj_id,
        plat_id,
        plat_name,
        plat_code,
        plat_other,
        url,
        stat_id,
        stat_name,
        stat_code,
        inv_id,
        inv_name,
        inv_code,
        notes,
        rule_out,
        first,
        last,
    ) in rows:
        items.append({
            "id": encode_id("social_media", int(sm_id)),
            "subject": {
                "id": encode_id("subject", int(subj_id)) if subj_id is not None else None,
                "first_name": first,
                "last_name": last,
            },
            "platform_id": encode_id("ref_value", int(plat_id)) if plat_id is not None else None,
            "platform_name": plat_name,
            "platform_code": plat_code,
            "platform_other": plat_other,
            "url": url,
            "status_id": encode_id("ref_value", int(stat_id)) if stat_id is not None else None,
            "status_name": stat_name,
            "status_code": stat_code,
            "investigated_id": encode_id("ref_value", int(inv_id)) if inv_id is not None else None,
            "investigated_name": inv_name,
            "investigated_code": inv_code,
            "notes": notes,
            "rule_out": bool(rule_out) if rule_out is not None else False,
        })

    return items


@router.post(
    "/{case_id}/social-media",
    summary="Create a social media row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_social_media(
    case_id: str,
    payload: SocialMediaCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    subj_db_id = None
    if getattr(payload, "subject_id", None) not in (None, ""):
        try:
            subj_db_id = decode_id("subject", payload.subject_id)
        except OpaqueIdError:
            raise HTTPException(status_code=404, detail="Subject not found")

        subj_exists = (await db.execute(select(Subject.id).where(Subject.id == int(subj_db_id)))).scalar_one_or_none()
        if subj_exists is None:
            raise HTTPException(status_code=404, detail="Subject not found")

    def _dec_ref(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s))
        except Exception:
            return None

    row = SocialMedia(
        case_id=int(case_db_id),
        subject_id=(int(subj_db_id) if subj_db_id is not None else None),
        platform_id=_dec_ref(getattr(payload, "platform_id", None)),
        platform_other=getattr(payload, "platform_other", None),
        url=getattr(payload, "url", None),
        status_id=_dec_ref(getattr(payload, "status_id", None)),
        investigated_id=_dec_ref(getattr(payload, "investigated_id", None)),
        notes=getattr(payload, "notes", None),
        rule_out=bool(getattr(payload, "rule_out", False)),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


class SocialMediaPartial(BaseModel):
    subject_id: _OptionalForSM[str] = None
    platform_id: _OptionalForSM[str] = None
    platform_other: _OptionalForSM[str] = None
    url: _OptionalForSM[str] = None
    status_id: _OptionalForSM[str] = None
    investigated_id: _OptionalForSM[str] = None
    notes: _OptionalForSM[str] = None
    rule_out: _OptionalForSM[bool] = None


@router.patch("/{case_id}/social-media/{social_media_id}", summary="Update a social media row for a case")
async def update_social_media(
    case_id: str,
    social_media_id: str,
    payload: SocialMediaPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    row = (
        await db.execute(
            select(SocialMedia).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    def _dec_ref(oid: _OptionalForSM[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s))
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "subject_id" in fields_set and payload.subject_id is not None:
        try:
            row.subject_id = int(decode_id("subject", payload.subject_id))
        except Exception:
            pass
    if "platform_id" in fields_set:
        row.platform_id = _dec_ref(payload.platform_id)
    if "platform_other" in fields_set:
        row.platform_other = payload.platform_other
    if "url" in fields_set:
        row.url = payload.url
    if "status_id" in fields_set:
        row.status_id = _dec_ref(payload.status_id)
    if "investigated_id" in fields_set:
        row.investigated_id = _dec_ref(payload.investigated_id)
    if "notes" in fields_set:
        row.notes = payload.notes
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}


# -------- Social Media Aliases (social_media_alias) --------
from app.db.models.social_media_alias import SocialMediaAlias
from app.db.models.ref_type import RefType

class SocialMediaAliasCreate(BaseModel):
    alias_status_id: Optional[str] = None
    alias: Optional[str] = None
    alias_owner_id: Optional[str] = None

class SocialMediaAliasPartial(BaseModel):
    alias_status_id: Optional[str] = None
    alias: Optional[str] = None
    alias_owner_id: Optional[str] = None

@router.get("/{case_id}/social-media/{social_media_id}/aliases", summary="List aliases for a social media record")
async def list_social_media_aliases(
    case_id: str,
    social_media_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    # Ensure the social media record belongs to this case
    sm_row = (
        await db.execute(select(SocialMedia.id).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    StatRV = aliased(RefValue)
    q = (
        select(
            SocialMediaAlias.id.label("alias_id"),
            SocialMediaAlias.alias_status_id,
            StatRV.name.label("alias_status_name"),
            StatRV.code.label("alias_status_code"),
            SocialMediaAlias.alias,
            SocialMediaAlias.alias_owner_id,
        )
        .join(StatRV, StatRV.id == SocialMediaAlias.alias_status_id, isouter=True)
        .where(SocialMediaAlias.social_media_id == int(sm_db_id))
        .order_by(asc(SocialMediaAlias.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for alias_id, status_id, status_name, status_code, alias, alias_owner_id in rows:
        items.append({
            "id": encode_id("social_media_alias", int(alias_id)),
            "alias_status_id": encode_id("ref_value", int(status_id)) if status_id is not None else None,
            "alias_status_name": status_name,
            "alias_status_code": status_code,
            "alias": alias,
            "alias_owner_id": encode_id("person", int(alias_owner_id)) if alias_owner_id is not None else None,
        })
    return items

@router.post(
    "/{case_id}/social-media/{social_media_id}/aliases",
    summary="Create an alias for a social media record",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_social_media_alias(
    case_id: str,
    social_media_id: str,
    payload: SocialMediaAliasCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Social media record not found")

    sm_row = (
        await db.execute(select(SocialMedia).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    # Decode optional fields
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

    def _dec_person(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("person", s))
        except Exception:
            return None

    status_id = _dec_ref(getattr(payload, "alias_status_id", None))

    # If no status provided, default to SM_ALIAS:NA
    if status_id is None:
        # Find the ref value for SM_ALIAS code 'NA'
        rv = (
            await db.execute(
                select(RefValue.id)
                .join(RefType, RefType.id == RefValue.ref_type_id)
                .where(RefValue.code == "NA", RefType.code == "SM_ALIAS")
                .limit(1)
            )
        ).scalar_one_or_none()
        # Fallback: first SM_ALIAS value if NA is not found
        if rv is None:
            rv = (
                await db.execute(
                    select(RefValue.id)
                    .join(RefType, RefType.id == RefValue.ref_type_id)
                    .where(RefType.code == "SM_ALIAS")
                    .order_by(asc(RefValue.sort_order), asc(RefValue.id))
                    .limit(1)
                )
            ).scalar_one_or_none()
        status_id = int(rv) if rv is not None else None

    if status_id is None:
        # As a last resort, reject if we couldn't resolve a default
        raise HTTPException(status_code=400, detail="Unable to resolve default alias status")

    owner_id = _dec_person(getattr(payload, "alias_owner_id", None))

    row = SocialMediaAlias(
        social_media_id=int(sm_db_id),
        alias_status_id=int(status_id),
        alias=getattr(payload, "alias", None),
        alias_owner_id=(int(owner_id) if owner_id is not None else None),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}

@router.patch(
    "/{case_id}/social-media/{social_media_id}/aliases/{alias_id}",
    summary="Update an alias for a social media record",
)
async def update_social_media_alias(
    case_id: str,
    social_media_id: str,
    alias_id: str,
    payload: SocialMediaAliasPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        sm_db_id = decode_id("social_media", social_media_id)
        alias_db_id = decode_id("social_media_alias", alias_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Record not found")

    # Ensure the social media record belongs to this case
    sm_row = (
        await db.execute(select(SocialMedia.id).where(SocialMedia.id == int(sm_db_id), SocialMedia.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if sm_row is None:
        raise HTTPException(status_code=404, detail="Social media record not found")

    # Load alias row and ensure it belongs to the social media record
    alias_row = (
        await db.execute(
            select(SocialMediaAlias).where(
                SocialMediaAlias.id == int(alias_db_id),
                SocialMediaAlias.social_media_id == int(sm_db_id),
            )
        )
    ).scalar_one_or_none()
    if alias_row is None:
        raise HTTPException(status_code=404, detail="Alias not found")

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

    def _dec_person(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("person", s))
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "alias_status_id" in fields_set:
        alias_row.alias_status_id = _dec_ref(payload.alias_status_id) or alias_row.alias_status_id
    if "alias" in fields_set:
        alias_row.alias = payload.alias
    if "alias_owner_id" in fields_set:
        alias_row.alias_owner_id = _dec_person(payload.alias_owner_id)

    await db.commit()
    return {"ok": True}


# -------- Timeline (timeline) --------
from datetime import date as _Date, time as _Time
from typing import Optional as _OptionalForTL
from app.db.models.timeline import Timeline
from app.db.models.intel_activity import IntelActivity


@router.get("/{case_id}/timeline", summary="List timeline entries for a case")
async def list_timeline(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Join Subject for who display and RefValue for type
    type_ref = aliased(RefValue)
    q = (
        select(
            Timeline.id,
            Timeline.date,
            Timeline.time,
            Timeline.who_id,
            Timeline.where,
            Timeline.details,
            Timeline.rule_out,
            Timeline.type_id,
            Timeline.type_other,
            Timeline.comments,
            Timeline.questions,
            Subject.first_name,
            Subject.last_name,
            type_ref.name,
            type_ref.code,
        )
        .join(Subject, Subject.id == Timeline.who_id, isouter=True)
        .join(type_ref, type_ref.id == Timeline.type_id, isouter=True)
        .where(Timeline.case_id == int(case_db_id))
        .order_by(asc(Timeline.date), asc(Timeline.time), asc(Timeline.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        tl_id,
        dt,
        tm,
        who_id,
        where,
        details,
        rule_out,
        type_id,
        type_other,
        comments,
        questions,
        first,
        last,
        type_name,
        type_code,
    ) in rows:
        items.append({
            "id": encode_id("timeline", int(tl_id)),
            "date": dt,
            "time": tm,
            "who_id": encode_id("subject", int(who_id)) if who_id is not None else None,
            "who_name": (f"{first or ''} {last or ''}".strip() if (first or last) else None),
            "where": where,
            "details": details,
            "rule_out": bool(rule_out) if rule_out is not None else False,
            "type_id": encode_id("ref_value", int(type_id)) if type_id is not None else None,
            "type_other": type_other,
            "type_name": type_name,
            "type_code": type_code,
            "comments": comments,
            "questions": questions,
        })

    return items


class TimelinePartial(BaseModel):
    date: _OptionalForTL[str] = None  # YYYY-MM-DD
    time: _OptionalForTL[str] = None  # HH:MM[:SS]
    who_id: _OptionalForTL[str] = None  # opaque subject id or null/empty to clear
    where: _OptionalForTL[str] = None
    details: _OptionalForTL[str] = None
    comments: _OptionalForTL[str] = None
    questions: _OptionalForTL[str] = None
    type_id: _OptionalForTL[str] = None  # opaque ref_value id or empty/null to clear
    type_other: _OptionalForTL[str] = None
    rule_out: _OptionalForTL[bool] = None


@router.patch("/{case_id}/timeline/{timeline_id}", summary="Update a timeline row for a case")
async def update_timeline(
    case_id: str,
    timeline_id: str,
    payload: TimelinePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        tl_db_id = decode_id("timeline", timeline_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Timeline record not found")

    row = (
        await db.execute(
            select(Timeline).where(Timeline.id == int(tl_db_id), Timeline.case_id == int(case_db_id))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Timeline record not found")

    def _parse_date(s: _OptionalForTL[str]):
        if s is None:
            return row.date
        if str(s) == "":
            return None
        try:
            return _Date.fromisoformat(str(s))
        except Exception:
            return row.date

    def _parse_time(s: _OptionalForTL[str]):
        if s is None:
            return row.time
        if str(s) == "":
            return None
        try:
            return _Time.fromisoformat(str(s))
        except Exception:
            return row.time

    def _dec_subject(oid: _OptionalForTL[str]):
        if oid is None:
            return row.who_id
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("subject", s))
        except Exception:
            return row.who_id

    def _dec_ref(oid: _OptionalForTL[str], current_val: _OptionalForTL[int]):
        if oid is None:
            return current_val
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s))
        except Exception:
            return current_val

    fields_set = getattr(payload, "model_fields_set", set())

    if "date" in fields_set:
        row.date = _parse_date(payload.date)
    if "time" in fields_set:
        row.time = _parse_time(payload.time)
    if "who_id" in fields_set:
        row.who_id = _dec_subject(payload.who_id)
    if "where" in fields_set:
        row.where = payload.where
    if "details" in fields_set:
        row.details = payload.details
    if "comments" in fields_set:
        row.comments = payload.comments
    if "questions" in fields_set:
        row.questions = payload.questions
    if "type_id" in fields_set:
        row.type_id = _dec_ref(payload.type_id, row.type_id)
    if "type_other" in fields_set:
        row.type_other = payload.type_other
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}


@router.post(
    "/{case_id}/timeline",
    summary="Create a timeline row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_timeline(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Pick an arbitrary person linked to the case to satisfy entered_by_id
    pc = (
        await db.execute(
            select(PersonCase.person_id).where(PersonCase.case_id == int(case_db_id)).order_by(asc(PersonCase.id)).limit(1)
        )
    ).scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=400, detail="No person linked to case to attribute entry")

    row = Timeline(
        case_id=int(case_db_id),
        entered_by_id=int(pc),
        date=None,
        time=None,
        type_id=None,
        type_other=None,
        details=None,
        comments=None,
        where=None,
        who_id=None,
        questions=None,
        rule_out=False,
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


# -------- Intel Activity (intel_activity) --------
from typing import Optional as _OptionalForIA


@router.get("/{case_id}/activity", summary="List activity entries for a case")
async def list_activity(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Join RefValue for source and reported_to names/codes
    src = aliased(RefValue)
    rep = aliased(RefValue)
    q = (
        select(
            IntelActivity.id,
            IntelActivity.date,
            IntelActivity.what,
            IntelActivity.source_id,
            IntelActivity.source_other,
            IntelActivity.findings,
            IntelActivity.case_management,
            IntelActivity.reported_to,
            IntelActivity.reported_to_other,
            IntelActivity.on_eod_report,
            IntelActivity.rule_out,
            src.name,
            src.code,
            rep.name,
            rep.code,
        )
        .join(src, src.id == IntelActivity.source_id, isouter=True)
        .join(rep, rep.id == IntelActivity.reported_to, isouter=True)
        .where(IntelActivity.case_id == int(case_db_id))
        .order_by(asc(IntelActivity.date), asc(IntelActivity.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        ia_id,
        dt,
        what,
        source_id,
        source_other,
        findings,
        case_management,
        reported_to,
        reported_to_other,
        on_eod_report,
        rule_out,
        source_name,
        source_code,
        reported_to_name,
        reported_to_code,
    ) in rows:
        items.append({
            "id": encode_id("intel_activity", int(ia_id)),
            "date": dt,
            "what": what,
            "source_id": encode_id("ref_value", int(source_id)) if source_id is not None else None,
            "source_name": source_name,
            "source_code": source_code,
            "source_other": source_other,
            "findings": findings,
            "case_management": case_management,
            "reported_to": encode_id("ref_value", int(reported_to)) if reported_to is not None else None,
            "reported_to_name": reported_to_name,
            "reported_to_code": reported_to_code,
            "reported_to_other": reported_to_other,
            "on_eod_report": bool(on_eod_report) if on_eod_report is not None else False,
            "rule_out": bool(rule_out) if rule_out is not None else False,
        })

    return items


class IntelActivityPartial(BaseModel):
    date: _OptionalForIA[str] = None  # YYYY-MM-DD
    what: _OptionalForIA[str] = None
    source_id: _OptionalForIA[str] = None  # opaque ref_value id
    source_other: _OptionalForIA[str] = None
    findings: _OptionalForIA[str] = None
    case_management: _OptionalForIA[str] = None
    reported_to: _OptionalForIA[str] = None  # opaque ref_value id
    reported_to_other: _OptionalForIA[str] = None
    on_eod_report: _OptionalForIA[bool] = None
    rule_out: _OptionalForIA[bool] = None


@router.patch("/{case_id}/activity/{activity_id}", summary="Update an activity row for a case")
async def update_activity(
    case_id: str,
    activity_id: str,
    payload: IntelActivityPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        ia_db_id = decode_id("intel_activity", activity_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Activity record not found")

    row = (
        await db.execute(
            select(IntelActivity).where(IntelActivity.id == int(ia_db_id), IntelActivity.case_id == int(case_db_id))
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Activity record not found")

    def _parse_date(s: _OptionalForIA[str]):
        if s is None:
            return row.date
        if str(s) == "":
            return row.date  # keep existing because column non-nullable
        try:
            return Date.fromisoformat(str(s))
        except Exception:
            return row.date

    def _dec_ref(oid: _OptionalForIA[str], current_val: _OptionalForIA[int]):
        if oid is None:
            return current_val
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s))
        except Exception:
            return current_val

    fields_set = getattr(payload, "model_fields_set", set())

    if "date" in fields_set:
        row.date = _parse_date(payload.date)
    if "what" in fields_set:
        row.what = payload.what
    if "source_id" in fields_set:
        row.source_id = _dec_ref(payload.source_id, row.source_id)
    if "source_other" in fields_set:
        row.source_other = payload.source_other
    if "findings" in fields_set:
        row.findings = payload.findings
    if "case_management" in fields_set:
        row.case_management = payload.case_management
    if "reported_to" in fields_set:
        row.reported_to = _dec_ref(payload.reported_to, row.reported_to)
    if "reported_to_other" in fields_set:
        row.reported_to_other = payload.reported_to_other
    if "on_eod_report" in fields_set:
        row.on_eod_report = bool(payload.on_eod_report) if payload.on_eod_report is not None else False
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}


@router.post(
    "/{case_id}/activity",
    summary="Create an activity row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_activity(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Pick an arbitrary person linked to the case to satisfy entered_by_id
    pc = (
        await db.execute(
            select(PersonCase.person_id).where(PersonCase.case_id == int(case_db_id)).order_by(asc(PersonCase.id)).limit(1)
        )
    ).scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=400, detail="No person linked to case to attribute entry")

    row = IntelActivity(
        case_id=int(case_db_id),
        entered_by_id=int(pc),
        date=Date.today(),
        what=None,
        source_id=None,
        source_other=None,
        findings=None,
        case_management=None,
        reported_to=None,
        reported_to_other=None,
        on_eod_report=False,
        rule_out=False,
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


# ---------------- Images (list and upload) ----------------
@router.get("/{case_id}/images", summary="List images for a case")
async def list_images(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    # Access control (allow admins with CASES.ALL_CASES)
    if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
        if not await can_user_access_case(db, current_user.id, pk):
            raise HTTPException(status_code=404, detail="Case not found")

    # Join to gather creator/rfi names
    P = PersonModel
    R = Rfi
    I = Image
    q = (
        select(
            I.id,
            I.case_id,
            I.file_name,
            I.created_by_id,
            I.source_url,
            I.where,
            I.notes,
            I.rfi_id,
            I.created_at,
            I.updated_at,
            I.mime_type,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(I)
        .join(P, P.id == I.created_by_id, isouter=True)
        .join(R, R.id == I.rfi_id, isouter=True)
        .where(I.case_id == pk)
        .order_by(sa.desc(I.created_at))
    )

    rows = (await db.execute(q)).all()
    items = []
    for r in rows:
        rid = int(r.id)
        items.append({
            "id": rid,
            "case_id": int(r.case_id),
            "file_name": r.file_name,
            "created_by_id": int(r.created_by_id) if r.created_by_id is not None else None,
            "source_url": r.source_url,
            "where": r.where,
            "notes": r.notes,
            "rfi_id": int(r.rfi_id) if r.rfi_id is not None else None,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "mime_type": r.mime_type,
            # presigned links to S3 objects
            "url": get_download_link("image", rid, file_type=None, thumbnail=False, attachment_filename=r.file_name or "download"),
            "thumb": get_download_link("image", rid, file_type=None, thumbnail=True),
            "storage_slug": None,
            # extras for UI display
            "created_by_name": r.created_by_name if getattr(r, "created_by_name", None) else None,
            "rfi_name": r.rfi_name if getattr(r, "rfi_name", None) else None,
        })
    return items


@router.post("/{case_id}/images/upload", summary="Upload image for a case")
async def upload_image(
    case_id: str,
    file: UploadFile = UploadFileParam(...),
    thumbnail: Optional[UploadFile] = UploadFileParam(None),
    source_url: Optional[str] = Form(None),
    where: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    rfi_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    # Access control (allow admins with CASES.ALL_CASES)
    if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
        if not await can_user_access_case(db, current_user.id, pk):
            raise HTTPException(status_code=404, detail="Case not found")

    # Decode optional rfi_id if provided (opaque)
    rid: Optional[int] = None
    if rfi_id:
        try:
            rid = decode_id("rfi", rfi_id)
        except OpaqueIdError:
            rid = None

    # Resolve current user's person.id via Person.app_user_id
    person_id = None
    try:
        res = await db.execute(select(PersonModel.id).where(PersonModel.app_user_id == current_user.id))
        person_id = res.scalar()
    except Exception:
        person_id = None

    # Create DB row first to get the ID
    img = Image(
        case_id=pk,
        file_name=file.filename or "upload",
        created_by_id=int(person_id) if person_id is not None else None,
        source_url=source_url,
        where=where,
        notes=notes,
        rfi_id=rid,
    )
    db.add(img)
    await db.flush()  # assign PK

    # Store file in S3 under key image-<id>
    # Ensure we can read file bytes. UploadFile exposes .file as SpooledTemporaryFile
    file.file.seek(0)
    await create_file("image", img.id, file.file, content_type=file.content_type or "application/octet-stream")

    # Optional: store thumbnail alongside
    if thumbnail is not None:
        try:
            thumbnail.file.seek(0)
            # Always JPEG per requirement
            await create_file("image", img.id, thumbnail.file, content_type="image/jpeg", is_thumbnail=True)
        except Exception:
            # Non-fatal if thumbnail upload fails
            pass

    await db.commit()
    await db.refresh(img)

    # Build response payload with presigned URLs
    payload = {
        "id": int(img.id),
        "case_id": int(img.case_id),
        "file_name": img.file_name,
        "created_by_id": int(img.created_by_id) if img.created_by_id is not None else None,
        "source_url": img.source_url,
        "where": img.where,
        "notes": img.notes,
        "rfi_id": int(img.rfi_id) if img.rfi_id is not None else None,
        "created_at": img.created_at,
        "updated_at": img.updated_at,
        "url": get_download_link("image", int(img.id), file_type=file.content_type or None, thumbnail=False, attachment_filename=img.file_name or "download"),
        "thumb": get_download_link("image", int(img.id), file_type=None, thumbnail=True),
        "storage_slug": None,
    }
    return payload


@router.patch("/{case_id}/images/{image_id}", summary="Update image fields for a case")
async def update_image(
    case_id: str,
    image_id: str,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Update editable fields on an image: source_url, where, notes, rfi_id (opaque).
    Returns the updated record in the same shape used by list_images.
    """
    pk = _decode_or_404("case", case_id)
    # Access control
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        iid = decode_id("image", image_id) if not str(image_id).isdigit() else int(image_id)
    except OpaqueIdError:
        # Allow numeric IDs as well
        raise HTTPException(status_code=404, detail="Image not found")

    # Fetch image and validate ownership to case
    result = await db.execute(select(Image).where(Image.id == iid, Image.case_id == pk))
    img: Optional[Image] = result.scalars().first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    # Apply updates
    if payload is None:
        payload = {}
    source_url = payload.get("source_url")
    where = payload.get("where")
    notes = payload.get("notes")
    rfi_eid = payload.get("rfi_id")

    # Decode rfi opaque ID if provided
    rid: Optional[int] = img.rfi_id
    if rfi_eid is not None:
        if rfi_eid == "" or rfi_eid is None:
            rid = None
        else:
            try:
                rid = decode_id("rfi", rfi_eid) if not str(rfi_eid).isdigit() else int(rfi_eid)
            except OpaqueIdError:
                rid = None

    # Only set provided fields (allow nulls)
    if "source_url" in payload:
        img.source_url = source_url
    if "where" in payload:
        img.where = where
    if "notes" in payload:
        img.notes = notes
    if "rfi_id" in payload:
        img.rfi_id = rid

    await db.commit()
    await db.refresh(img)

    # Join to get names for response
    P = PersonModel
    R = Rfi
    I = Image
    q = (
        select(
            I.id,
            I.case_id,
            I.file_name,
            I.created_by_id,
            I.source_url,
            I.where,
            I.notes,
            I.rfi_id,
            I.created_at,
            I.updated_at,
            I.mime_type,
            (P.first_name + sa.literal(" ") + P.last_name).label("created_by_name"),
            R.name.label("rfi_name"),
        )
        .select_from(I)
        .join(P, P.id == I.created_by_id, isouter=True)
        .join(R, R.id == I.rfi_id, isouter=True)
        .where(I.id == img.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to load updated image")

    return {
        "id": int(row.id),
        "case_id": int(row.case_id),
        "file_name": row.file_name,
        "created_by_id": int(row.created_by_id) if row.created_by_id is not None else None,
        "source_url": row.source_url,
        "where": row.where,
        "notes": row.notes,
        "rfi_id": int(row.rfi_id) if row.rfi_id is not None else None,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "url": get_download_link("image", int(row.id), file_type=None, thumbnail=False, attachment_filename=row.file_name or "download"),
        "thumb": get_download_link("image", int(row.id), file_type=None, thumbnail=True),
        "mime_type" : row.mime_type,
        "storage_slug": None,
        "created_by_name": row.created_by_name if getattr(row, "created_by_name", None) else None,
        "rfi_name": row.rfi_name if getattr(row, "rfi_name", None) else None,
    }
