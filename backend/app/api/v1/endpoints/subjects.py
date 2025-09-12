from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, asc, func, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.subject import Subject
from app.schemas.subject import SubjectRead, SubjectUpsert
from pydantic import BaseModel
from typing import Optional
from app.core.id_codec import encode_id, decode_id, OpaqueIdError
from app.db.models.subject_case import SubjectCase
from app.db.models.person import Person
from app.db.models.person_case import PersonCase
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.db.models.case import Case
from app.db.models.app_user import AppUser
from app.services.auth import user_has_permission
from app.db.models.file_subject import FileSubject
from app.db.models.file import File

# Simple authenticated listing for subjects
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post(
    "/subjects",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a subject",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_subject(payload: SubjectUpsert, db: AsyncSession = Depends(get_db)) -> SubjectRead:
    first = (payload.first_name or "").strip()
    last = (payload.last_name or "").strip()
    if not first or not last:
        raise HTTPException(status_code=400, detail="First name and last name are required")

    dangerous = bool(payload.dangerous) if payload.dangerous is not None else False
    danger_text = (payload.danger or None) if dangerous else None

    subj = Subject(
        first_name=first,
        last_name=last,
        nicknames=(payload.nicknames or None),
        phone=(payload.phone or None),
        email=(payload.email or None),
        dangerous=dangerous,
        danger=danger_text,
    )
    db.add(subj)
    await db.commit()
    await db.refresh(subj)
    return subj


async def _get_current_person_id(db: AsyncSession, current_user: AppUser) -> int | None:
    res = await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))
    pid = res.scalar_one_or_none()
    return int(pid) if pid is not None else None


def _subject_visibility_filter(person_id: int):
    """
    Build SQLAlchemy filter so that a Subject is included if it is attached to any case
    related to the given person via either person_case or team_case.
    Subject linkage to a case can be:
      - direct (case.subject_id)
      - via subject_case
      - via file_subject on any image file belonging to those cases
    """
    # Cases related directly to the person
    pc_case_ids = select(PersonCase.case_id).where(PersonCase.person_id == person_id)

    # Cases related via the person's teams
    tc_case_ids = select(TeamCase.case_id).join(PersonTeam, PersonTeam.team_id == TeamCase.team_id).where(PersonTeam.person_id == person_id)

    # Union of case ids
    union_case_ids = pc_case_ids.union(tc_case_ids)

    # Subjects related to those cases via subject_case
    sc_subject_ids = select(SubjectCase.subject_id).where(SubjectCase.case_id.in_(union_case_ids))

    # Subjects directly attached on the case.subject_id
    direct_subject_ids = select(Case.subject_id).where(Case.id.in_(union_case_ids))

    # Subjects appearing in image files for those cases (file_subject join file)
    img_subject_ids = (
        select(FileSubject.subject_id)
        .join(File, File.id == FileSubject.file_id)
        .where(File.case_id.in_(union_case_ids))
        .where(File.is_image.is_(True))
    )

    return or_(
        Subject.id.in_(sc_subject_ids),
        Subject.id.in_(direct_subject_ids),
        Subject.id.in_(img_subject_ids),
    )


@router.get("/subjects", response_model=List[SubjectRead], summary="List subjects")
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> List[SubjectRead]:
    # If user has ALL_SUBJECTS permission, bypass filtering entirely
    has_all = await user_has_permission(db, current_user.id, "CONTACTS.ALL_SUBJECTS")
    if has_all:
        q = select(Subject).order_by(asc(Subject.last_name), asc(Subject.first_name))
        result = await db.execute(q)
        return list(result.scalars().all())

    person_id = await _get_current_person_id(db, current_user)
    if person_id is None:
        # No linked person -> no subjects visible
        return []

    q = select(Subject).where(_subject_visibility_filter(person_id)).order_by(asc(Subject.last_name), asc(Subject.first_name))
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/subjects/select", summary="List subjects for selection with enriched display")
async def list_subjects_for_select(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # If user has ALL_SUBJECTS permission, we won't apply visibility filter
    has_all = await user_has_permission(db, current_user.id, "CONTACTS.ALL_SUBJECTS")

    person_id = await _get_current_person_id(db, current_user) if not has_all else None
    if not has_all and person_id is None:
        return []

    # Base: subject fields + has_pic boolean
    q = select(
        Subject.id,
        Subject.first_name,
        Subject.last_name,
        Subject.nicknames,
        Subject.phone,
        Subject.email,
        Subject.dangerous,
        Subject.danger,
        Subject.profile_pic.isnot(None).label("has_pic"),
        # any subject_case rows for this subject?
        func.count(SubjectCase.id).label("case_count"),
    ).join(SubjectCase, SubjectCase.subject_id == Subject.id, isouter=True)

    if not has_all:
        visibility_filter = _subject_visibility_filter(person_id)
        q = q.where(visibility_filter)

    q = q.group_by(
        Subject.id,
        Subject.first_name,
        Subject.last_name,
        Subject.nicknames,
        Subject.phone,
        Subject.email,
        Subject.dangerous,
        Subject.danger,
        Subject.profile_pic,
    )
    q = q.order_by(asc(Subject.last_name), asc(Subject.first_name))

    rows = (await db.execute(q)).all()

    items = []
    for sid, first, last, nicknames, phone, email, dangerous, danger, has_pic, case_count in rows:
        # Compose display name with nicknames inserted between first and last if present
        nickname_part = f' "{nicknames.strip()}"' if nicknames and str(nicknames).strip() else ""
        display_name = f"{first}{nickname_part} {last}".strip()
        items.append({
            "id": encode_id("subject", int(sid)),
            "name": display_name,
            "phone": phone,
            "email": email,
            "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(sid))}?s=sm" if has_pic else "/images/pfp-generic.png",
            "has_subject_case": (int(case_count or 0) > 0),
            "dangerous": bool(dangerous),
            "danger": danger,
        })

    return items


class SubjectPartial(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    nicknames: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    dangerous: Optional[bool] = None
    danger: Optional[str] = None

@router.patch(
    "/subjects/{subject_id}",
    response_model=SubjectRead,
    summary="Update a subject by opaque id",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def update_subject(
    subject_id: str,
    payload: SubjectPartial,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> SubjectRead:
    # Decode opaque subject id
    try:
        sid = decode_id("subject", subject_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Authorization: if user has ALL_SUBJECTS, allow; else ensure subject visible via cases
    if not await user_has_permission(db, current_user.id, "CONTACTS.ALL_SUBJECTS"):
        person_id = await _get_current_person_id(db, current_user)
        if person_id is None:
            raise HTTPException(status_code=404, detail="Subject not found")
        # Ensure the subject is within visibility filter
        vis_filter = _subject_visibility_filter(person_id)
        res = await db.execute(select(Subject.id).where(Subject.id == sid).where(vis_filter))
        if res.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Subject not found")

    # Load subject
    subj = (await db.execute(select(Subject).where(Subject.id == sid))).scalar_one_or_none()
    if subj is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Update allowed fields; trim strings and normalize empties to None where appropriate
    def _clean(s: str | None) -> str | None:
        if s is None:
            return None
        s2 = str(s).strip()
        return s2 if s2 else None

    # Update only fields explicitly provided in payload
    fields_set = getattr(payload, "model_fields_set", set())

    # Required fields on schema; keep existing if payload not provided (allow partial)
    if "first_name" in fields_set and payload.first_name is not None:
        subj.first_name = (payload.first_name or "").strip()
    if "last_name" in fields_set and payload.last_name is not None:
        subj.last_name = (payload.last_name or "").strip()
    # Optional fields
    if "middle_name" in fields_set:
        subj.middle_name = _clean(payload.middle_name)
    if "nicknames" in fields_set:
        subj.nicknames = _clean(payload.nicknames)
    if "phone" in fields_set:
        subj.phone = _clean(payload.phone)
    if "email" in fields_set:
        subj.email = _clean(payload.email)
    if "dangerous" in fields_set and payload.dangerous is not None:
        subj.dangerous = bool(payload.dangerous)
        # Reset danger text if not dangerous
        if not subj.dangerous:
            subj.danger = None
    if "danger" in fields_set:
        subj.danger = _clean(payload.danger)

    await db.commit()
    await db.refresh(subj)
    return subj
