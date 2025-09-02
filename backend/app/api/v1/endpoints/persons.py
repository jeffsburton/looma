from typing import List, Dict, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.person import Person
from app.db.models.organization import Organization
from app.db.models.person_team import PersonTeam
from app.db.models.team import Team
from app.core.id_codec import encode_id, decode_id, OpaqueIdError
from app.schemas.person import PersonRead, PersonUpsert
from pydantic import BaseModel

# Simple authenticated listing for person selection widgets
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/persons", response_model=List[PersonRead], summary="List people")
async def list_persons(db: AsyncSession = Depends(get_db)) -> List[PersonRead]:
    result = await db.execute(select(Person))
    return list(result.scalars().all())


@router.post(
    "/persons",
    response_model=PersonRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a person",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_person(payload: PersonUpsert, db: AsyncSession = Depends(get_db)) -> PersonRead:
    # Normalize organization_id: accept opaque token or raw int or null
    org_id_int = None
    if payload.organization_id is not None and payload.organization_id != "":
        try:
            if isinstance(payload.organization_id, str):
                # Try to decode opaque token
                org_id_int = decode_id("organization", payload.organization_id)
            else:
                # Assume int-like
                org_id_int = int(payload.organization_id)  # type: ignore[arg-type]
        except (ValueError, OpaqueIdError):
            raise HTTPException(status_code=400, detail="Invalid organization_id")

    person = Person(
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        phone=(payload.phone or None),
        email=(payload.email or None),
        telegram=getattr(payload, "telegram", None),
        organization_id=org_id_int,
    )
    db.add(person)
    await db.commit()
    await db.refresh(person)
    return person


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


class PersonPartial(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    telegram: Optional[str] = None
    organization_id: Optional[str] = None


@router.patch(
    "/persons/{person_id}",
    response_model=PersonRead,
    summary="Update a person by opaque id",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def update_person(
    person_id: str,
    payload: PersonPartial,
    db: AsyncSession = Depends(get_db),
):
    # Decode opaque person id
    try:
        pid = decode_id("person", person_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Person not found")

    # Load person
    person = (await db.execute(select(Person).where(Person.id == pid))).scalar_one_or_none()
    if person is None:
        raise HTTPException(status_code=404, detail="Person not found")

    # Helper to clean strings
    def _clean(s: Optional[str]) -> Optional[str]:
        if s is None:
            return None
        s2 = str(s).strip()
        return s2 if s2 else None

    # Update fields if provided
    if payload.first_name is not None:
        person.first_name = (payload.first_name or "").strip()
    if payload.last_name is not None:
        person.last_name = (payload.last_name or "").strip()
    if hasattr(payload, "phone"):
        person.phone = _clean(payload.phone)
    if hasattr(payload, "email"):
        person.email = _clean(payload.email)
    if hasattr(payload, "telegram"):
        person.telegram = _clean(payload.telegram)
    if hasattr(payload, "organization_id"):
        # Normalize organization_id: accept opaque token, raw int, empty/null
        org_raw = payload.organization_id
        if org_raw is None or org_raw == "":
            person.organization_id = None
        else:
            try:
                if isinstance(org_raw, str):
                    person.organization_id = int(decode_id("organization", org_raw))
                else:
                    person.organization_id = int(org_raw)  # type: ignore[arg-type]
            except (ValueError, OpaqueIdError):
                raise HTTPException(status_code=400, detail="Invalid organization_id")

    await db.commit()
    await db.refresh(person)
    return person