from typing import List, Dict, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, func

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.team import Team
from app.db.models.person import Person
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.db.models.case import Case
from app.db.models.subject import Subject
from app.db.models.event import Event
from app.schemas.team import TeamRead, TeamUpsert, TeamMemberSummary, TeamCaseSummary
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

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
        )
        .join(Person, Person.id == PersonTeam.person_id)
        .where(PersonTeam.team_id.in_(team_ids))
    )
    for team_id, person_id, first, last, has_pic in mres.all():
        name = f"{first} {last}".strip()
        photo_url = (
            f"/api/v1/media/pfp/person/{encode_id('person', int(person_id))}?s=xs"
            if has_pic else "/images/pfp-generic.png"
        )
        members_map[int(team_id)].append(TeamMemberSummary(id=int(person_id), name=name, photo_url=photo_url))

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
