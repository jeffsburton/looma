from typing import List, Dict, Tuple, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, func, asc
from sqlalchemy.sql import expression as sql_expr

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.team import Team
from app.db.models.person import Person
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.db.models.case import Case
from app.db.models.subject import Subject
from app.db.models.event import Event
from app.db.models.ref_value import RefValue
from app.schemas.team import TeamRead, TeamUpsert, TeamMemberSummary, TeamCaseSummary
from app.core.id_codec import decode_id, OpaqueIdError, encode_id


class MemberRoleUpdate(BaseModel):
    team_role_id: str

# All teams endpoints require TEAMS permission to view
router = APIRouter(dependencies=[Depends(require_permission("TEAMS"))])


@router.get("/teams", response_model=List[TeamRead], summary="List teams")
async def list_teams(db: AsyncSession = Depends(get_db)) -> List[TeamRead]:
    # Base teams
    team_result = await db.execute(select(Team))
    teams = list(team_result.scalars().all())
    if not teams:
        return []

    team_ids = [t.id for t in teams]

    # Event names map
    event_ids = [t.event_id for t in teams if t.event_id]
    event_name_map: Dict[int, str] = {}
    if event_ids:
        er = await db.execute(select(Event.id, Event.name).where(Event.id.in_(event_ids)))
        for eid, name in er.all():
            event_name_map[int(eid)] = name

    # Members by team
    members_map: Dict[int, List[TeamMemberSummary]] = {tid: [] for tid in team_ids}
    mres = await db.execute(
        select(
            PersonTeam.team_id,
            Person.id,
            Person.first_name,
            Person.last_name,
            Person.profile_pic.isnot(None).label("has_pic"),
            RefValue.name.label("role_name"),
            RefValue.id.label("role_id"),
            RefValue.code.label("role_code"),
            Person.phone,
            Person.email,
            Person.telegram,
        )
        .join(Person, Person.id == PersonTeam.person_id)
        .join(RefValue, RefValue.id == PersonTeam.team_role_id)
        .where(PersonTeam.team_id.in_(team_ids))
        .order_by(
            PersonTeam.team_id,
            sql_expr.nulls_last(asc(RefValue.sort_order)),
            asc(Person.last_name),
            asc(Person.first_name),
        )
    )
    for team_id, person_id, first, last, has_pic, role_name, role_id, role_code, phone, email, telegram in mres.all():
        name = f"{first} {last}".strip()
        photo_url = (
            f"/api/v1/media/pfp/person/{encode_id('person', int(person_id))}?s=xs"
            if has_pic else "/images/pfp-generic.png"
        )
        members_map[int(team_id)].append(
            TeamMemberSummary(
                id=int(person_id),
                name=name,
                photo_url=photo_url,
                role_name=role_name,
                role_id=encode_id('ref_value', int(role_id)) if role_id is not None else None,
                role_code=role_code,
                phone=phone,
                email=email,
                telegram=telegram,
            )
        )

    # Cases by team
    cases_map: Dict[int, List[TeamCaseSummary]] = {tid: [] for tid in team_ids}
    cres = await db.execute(
        select(
            TeamCase.team_id,
            Case.id.label("case_id"),
            Subject.id.label("subject_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.profile_pic.isnot(None).label("has_pic"),
        )
        .join(Case, Case.id == TeamCase.case_id)
        .join(Subject, Subject.id == Case.subject_id)
        .where(TeamCase.team_id.in_(team_ids))
    )
    for team_id, case_id, subject_id, first, last, has_pic in cres.all():
        name = f"{first} {last}".strip()
        photo_url = (
            f"/api/v1/media/pfp/subject/{encode_id('subject', int(subject_id))}?s=xs"
            if has_pic else "/images/pfp-generic.png"
        )
        cases_map[int(team_id)].append(TeamCaseSummary(id=int(case_id), name=name, photo_url=photo_url))

    # Attach
    enriched: List[Team] = []
    for t in teams:
        setattr(t, "event_name", event_name_map.get(t.event_id))
        # Team photo URL: use media endpoint if a blob exists; otherwise generic placeholder
        try:
            has_team_pic = bool(getattr(t, "profile_pic", None))
        except Exception:
            has_team_pic = False
        team_photo_url = (
            f"/api/v1/media/pfp/team/{encode_id('team', int(t.id))}?s=sm" if has_team_pic else "/images/pfp-generic.png"
        )
        setattr(t, "photo_url", team_photo_url)
        setattr(t, "members", members_map.get(t.id, []))
        setattr(t, "cases", cases_map.get(t.id, []))
        enriched.append(t)
    return enriched


@router.post(
    "/teams",
    response_model=TeamRead,
    summary="Create team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def create_team(payload: TeamUpsert, db: AsyncSession = Depends(get_db)) -> TeamRead:
    event_pk = None
    if payload.event_id is not None:
        try:
            event_pk = decode_id("event", payload.event_id)
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid event_id")

    obj = Team(
        name=payload.name,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
        event_id=event_pk,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()
    return obj


@router.put(
    "/teams/{id}",
    response_model=TeamRead,
    summary="Update team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def update_team(
    id: str = Path(..., description="Opaque team id"),
    payload: TeamUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> TeamRead:
    try:
        pk = decode_id("team", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    obj = await db.get(Team, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Team not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)
    if payload.event_id is not None:
        if payload.event_id == "":
            obj.event_id = None
        else:
            try:
                obj.event_id = decode_id("event", payload.event_id)
            except OpaqueIdError:
                raise HTTPException(status_code=400, detail="Invalid event_id")

    await db.flush()
    await db.refresh(obj)
    await db.commit()
    return obj


@router.put(
    "/teams/{team_id}/members/{person_id}",
    summary="Update a team member's role",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def update_team_member_role(
    team_id: str = Path(..., description="Opaque team id"),
    person_id: str = Path(..., description="Opaque person id or numeric id"),
    payload: MemberRoleUpdate = None,
    db: AsyncSession = Depends(get_db),
):
    # decode team id (opaque)
    try:
        team_pk = decode_id("team", team_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    # decode person id (allow opaque or raw int)
    try:
        person_pk = decode_id("person", person_id)
    except OpaqueIdError:
        try:
            person_pk = int(person_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Person not found")

    # decode role id
    try:
        role_pk = decode_id("ref_value", payload.team_role_id)
    except OpaqueIdError:
        raise HTTPException(status_code=400, detail="Invalid team_role_id")

    # find PersonTeam
    result = await db.execute(
        select(PersonTeam).where(
            PersonTeam.team_id == team_pk,
            PersonTeam.person_id == person_pk,
        )
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Membership not found")

    pt.team_role_id = role_pk
    await db.flush()
    await db.commit()
    return {"ok": True}


@router.delete(
    "/teams/{team_id}/members/{person_id}",
    summary="Remove a person from team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def delete_team_member(
    team_id: str = Path(..., description="Opaque team id"),
    person_id: str = Path(..., description="Opaque person id or numeric id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        team_pk = decode_id("team", team_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    try:
        person_pk = decode_id("person", person_id)
    except OpaqueIdError:
        try:
            person_pk = int(person_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Person not found")

    result = await db.execute(
        select(PersonTeam).where(
            PersonTeam.team_id == team_pk,
            PersonTeam.person_id == person_pk,
        )
    )
    pt = result.scalar_one_or_none()
    if not pt:
        # Treat as idempotent
        return {"ok": True}

    await db.delete(pt)
    await db.flush()
    await db.commit()
    return {"ok": True}


class AddMemberPayload(BaseModel):
    person_id: str
    team_role_id: Optional[str] = None


@router.post(
    "/teams/{team_id}/members",
    summary="Add a person to team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def add_team_member(
    team_id: str = Path(..., description="Opaque team id"),
    payload: AddMemberPayload = None,
    db: AsyncSession = Depends(get_db),
):
    # decode team id
    try:
        team_pk = decode_id("team", team_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    # decode person id (allow opaque or raw int)
    try:
        person_pk = decode_id("person", payload.person_id)
    except OpaqueIdError:
        try:
            person_pk = int(payload.person_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid person_id")

    # determine role id: default to 143 if not provided
    role_pk: int
    if payload.team_role_id:
        try:
            role_pk = decode_id("ref_value", payload.team_role_id)
        except OpaqueIdError:
            try:
                role_pk = int(payload.team_role_id)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid team_role_id")
    else:
        role_pk = 143

    # prevent duplicates
    res = await db.execute(
        select(PersonTeam).where(
            PersonTeam.team_id == team_pk,
            PersonTeam.person_id == person_pk,
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        # Treat as idempotent add
        return {"ok": True}

    pt = PersonTeam(team_id=team_pk, person_id=person_pk, team_role_id=role_pk)
    db.add(pt)
    await db.flush()
    await db.commit()
    return {"ok": True}


# ---- Team Cases management ----
class AddCasePayload(BaseModel):
    case_id: str


@router.post(
    "/teams/{team_id}/cases",
    summary="Add a case to team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def add_team_case(
    team_id: str = Path(..., description="Opaque team id"),
    payload: AddCasePayload = None,
    db: AsyncSession = Depends(get_db),
):
    # decode team id
    try:
        team_pk = decode_id("team", team_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    # decode case id (allow opaque or raw int)
    try:
        case_pk = decode_id("case", payload.case_id)
    except OpaqueIdError:
        try:
            case_pk = int(payload.case_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid case_id")

    # prevent duplicates
    res = await db.execute(
        select(TeamCase).where(
            TeamCase.team_id == team_pk,
            TeamCase.case_id == case_pk,
        )
    )
    existing = res.scalar_one_or_none()
    if existing:
        # idempotent
        return {"ok": True}

    tc = TeamCase(team_id=team_pk, case_id=case_pk)
    db.add(tc)
    await db.flush()
    await db.commit()
    return {"ok": True}


@router.delete(
    "/teams/{team_id}/cases/{case_id}",
    summary="Remove a case from team",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def delete_team_case(
    team_id: str = Path(..., description="Opaque team id"),
    case_id: str = Path(..., description="Opaque case id or numeric id"),
    db: AsyncSession = Depends(get_db),
):
    try:
        team_pk = decode_id("team", team_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    try:
        case_pk = decode_id("case", case_id)
    except OpaqueIdError:
        try:
            case_pk = int(case_id)
        except Exception:
            raise HTTPException(status_code=404, detail="Case not found")

    result = await db.execute(
        select(TeamCase).where(
            TeamCase.team_id == team_pk,
            TeamCase.case_id == case_pk,
        )
    )
    tc = result.scalar_one_or_none()
    if not tc:
        return {"ok": True}

    await db.delete(tc)
    await db.flush()
    await db.commit()
    return {"ok": True}


@router.post(
    "/teams/{id}/profile_pic",
    summary="Upload team profile picture",
    dependencies=[Depends(require_permission("TEAMS.MODIFY"))],
)
async def upload_team_profile_pic(
    id: str = Path(..., description="Opaque team id"),
    file: UploadFile = File(..., description="Image file for team profile picture"),
    db: AsyncSession = Depends(get_db),
):
    try:
        pk = decode_id("team", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Team not found")

    obj = await db.get(Team, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Team not found")

    # Read and validate file (basic size/type checks)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    max_bytes = 5 * 1024 * 1024  # 5MB
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large (max 5MB)")

    # Validate it's an image by magic numbers
    is_image = (
        content.startswith(b"\x89PNG\r\n\x1a\n") or
        content.startswith(b"\xff\xd8\xff") or
        content.startswith(b"GIF8") or
        (content[:4] == b"RIFF" and b"WEBP" in content[:32])
    )
    if not is_image:
        raise HTTPException(status_code=400, detail="Unsupported image format")

    obj.profile_pic = content

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    return {"ok": True}
