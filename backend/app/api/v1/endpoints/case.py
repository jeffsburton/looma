from typing import List, Optional
from datetime import date as Date

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc, exists, or_, and_
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.api.dependencies import get_current_user
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
from app.schemas.case_demographics import CaseDemographicsRead, CaseDemographicsUpsert
from app.schemas.case_management import CaseManagementUpsert
from app.schemas.case_pattern_of_life import CasePatternOfLifeUpsert


router = APIRouter(prefix="/cases")


# ---------- Helper utilities ----------

def _decode_or_404(model: str, opaque_id: str) -> int:
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

    # Fetch joins: subject, demographics, circumstances, management + ref codes
    SexRV = aliased(RefValue)
    RaceRV = aliased(RefValue)
    CsecRV = aliased(RefValue)
    MstatRV = aliased(RefValue)
    MclassRV = aliased(RefValue)

    q = (
        select(
            Case.id.label("case_id"),
            Case.case_number,
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
            CsecRV.code.label("csec_code"),
            MstatRV.code.label("missing_status_code"),
            MclassRV.code.label("classification_code"),
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
        .join(CasePatternOfLife, CasePatternOfLife.case_id == Case.id, isouter=True)
        .where(Case.id == case_row.id)
    )
    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")

    (
        case_id,
        case_number_val,
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
    ) = row

    subject_opaque = encode_id("subject", int(subject_id))
    case_opaque = encode_id("case", int(case_id))

    return {
        "case": {
            "id": case_opaque,
            "raw_db_id": int(case_id),
            "case_number": case_number_val,
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
            "csec_code": csec_code,
            "missing_status_code": missing_status_code,
            "classification_code": classification_code,
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
