from typing import List, Optional
from datetime import date as Date

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc, exists, or_, and_
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
from app.schemas.case_demographics import CaseDemographicsRead, CaseDemographicsUpsert


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

    # Fetch joins: subject, demographics, circumstances
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
            CaseCircumstances.date_missing,
        )
        .join(Subject, Subject.id == Case.subject_id)
        .join(CaseDemographics, CaseDemographics.case_id == Case.id, isouter=True)
        .join(CaseCircumstances, CaseCircumstances.case_id == Case.id, isouter=True)
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
        date_missing,
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
        },
        "circumstances": {
            "date_missing": date_missing.isoformat() if date_missing is not None else None,
        },
    }
