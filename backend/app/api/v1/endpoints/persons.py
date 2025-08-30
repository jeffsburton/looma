from typing import List, Dict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, and_, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.person import Person
from app.db.models.organization import Organization
from app.db.models.person_team import PersonTeam
from app.db.models.team import Team
from app.core.id_codec import encode_id
from app.schemas.person import PersonRead

# Simple authenticated listing for person selection widgets
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/persons", response_model=List[PersonRead], summary="List people")
async def list_persons(db: AsyncSession = Depends(get_db)) -> List[PersonRead]:
    result = await db.execute(select(Person))
    return list(result.scalars().all())


@router.get("/persons/select", summary="List people for selection with enriched display")
async def list_persons_for_select(
    shepherds: bool = Query(True, description="Include persons where organization_id == 1"),
    non_shepherds: bool = Query(True, description="Include persons where organization_id > 1"),
    db: AsyncSession = Depends(get_db),
):
    if not shepherds and not non_shepherds:
        raise HTTPException(status_code=400, detail="At least one of shepherds or non_shepherds must be true")

    # Base people with org
    where_clause = []
    if shepherds and not non_shepherds:
        where_clause.append(Person.organization_id == 1)
    elif non_shepherds and not shepherds:
        where_clause.append(or_(Person.organization_id == None, Person.organization_id > 1))
    # If both true, include all (no extra where clause)

    q = select(
        Person.id,
        Person.first_name,
        Person.last_name,
        Person.phone,
        Person.email,
        Person.telegram,
        Person.profile_pic.isnot(None).label("has_pic"),
        Person.organization_id,
        Organization.name.label("org_name"),
    ).join(Organization, Organization.id == Person.organization_id, isouter=True)

    if where_clause:
        q = q.where(and_(*where_clause))

    q = q.order_by(asc(Person.last_name), asc(Person.first_name))

    result = await db.execute(q)

    rows = result.all()

    # collect person ids for team pfps (for shepherds only)
    person_ids = [int(r[0]) for r in rows]
    team_pfp_map: Dict[int, List[str]] = {pid: [] for pid in person_ids}

    if person_ids:
        trows = await db.execute(
            select(
                PersonTeam.person_id,
                Team.id,
                Team.profile_pic.isnot(None).label("team_has_pic"),
                Team.inactive,
            ).where(PersonTeam.person_id.in_(person_ids)).join(Team, Team.id == PersonTeam.team_id)
        )
        for person_id, team_id, team_has_pic, inactive in trows.all():
            if inactive:
                continue
            if team_has_pic:
                team_pfp_map[int(person_id)].append(
                    f"/api/v1/media/pfp/team/{encode_id('team', int(team_id))}?s=xs"
                )

    # Build response items
    items = []
    for pid, first, last, phone, email, telegram, has_pic, org_id, org_name in rows:
        is_shep = (org_id == 1)
        items.append({
            "id": encode_id("person", int(pid)),
            "name": f"{first} {last}".strip(),
            "phone": phone,
            "email": email,
            "telegram": telegram,
            "photo_url": f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=sm" if has_pic else "/images/pfp-generic.png",
            "is_shepherd": is_shep,
            "organization_name": org_name,
            "team_photo_urls": team_pfp_map.get(int(pid), []) if is_shep else [],
        })

    return items
