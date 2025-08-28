from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.rfi_source import RfiSource
from app.db.models.person import Person
from app.schemas.rfi_source import RfiSourceRead, RfiSourceUpsert
from app.core.id_codec import decode_id, OpaqueIdError, encode_id


router = APIRouter(dependencies=[Depends(require_permission("RFI_SOURCES"))])


def _attach_person_display_and_ids(obj: RfiSource, p_primary: Optional[Person], p_backup: Optional[Person]):
    # Attach friendly names
    obj.primary_name = f"{p_primary.first_name} {p_primary.last_name}" if p_primary else None
    obj.backup_name = f"{p_backup.first_name} {p_backup.last_name}" if p_backup else None
    # Convert to opaque person IDs for the frontend selectors
    obj.primary_id = encode_id("person", int(p_primary.id)) if p_primary else None
    obj.backup_id = encode_id("person", int(p_backup.id)) if p_backup else None


@router.get("/rfi-sources", response_model=List[RfiSourceRead], summary="List RFI Sources")
async def list_rfi_sources(db: AsyncSession = Depends(get_db)) -> List[RfiSourceRead]:
    P1 = aliased(Person)
    P2 = aliased(Person)
    # join via Person.app_user_id to RfiSource.primary_id/backup_id
    stmt = (
        select(RfiSource, P1, P2)
        .join(P1, P1.app_user_id == RfiSource.primary_id, isouter=True)
        .join(P2, P2.app_user_id == RfiSource.backup_id, isouter=True)
    )
    result = await db.execute(stmt)
    rows: List[RfiSource] = []
    for src, p1, p2 in result.all():
        _attach_person_display_and_ids(src, p1, p2)
        rows.append(src)
    return rows


async def _person_to_app_user_id(db: AsyncSession, opaque_person_id: Optional[str]) -> Optional[int]:
    if not opaque_person_id:
        return None
    try:
        person_pk = decode_id("person", opaque_person_id)
    except OpaqueIdError:
        raise HTTPException(status_code=400, detail="Invalid person id")
    person = await db.get(Person, person_pk)
    if not person:
        raise HTTPException(status_code=400, detail="Invalid person id")
    # person may not be linked to an app_user; in that case store NULL
    return person.app_user_id or None


@router.post("/rfi-sources", response_model=RfiSourceRead, summary="Create RFI Source")
async def create_rfi_source(payload: RfiSourceUpsert, db: AsyncSession = Depends(get_db)) -> RfiSourceRead:
    primary_user_id = await _person_to_app_user_id(db, payload.primary_id)
    backup_user_id = await _person_to_app_user_id(db, payload.backup_id)

    obj = RfiSource(
        name=payload.name,
        description=payload.description,
        primary_id=primary_user_id,
        backup_id=backup_user_id,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()

    # attach display fields for response
    p1 = None
    p2 = None
    if obj.primary_id is not None:
        p1 = (await db.execute(select(Person).where(Person.app_user_id == obj.primary_id))).scalars().first()
    if obj.backup_id is not None:
        p2 = (await db.execute(select(Person).where(Person.app_user_id == obj.backup_id))).scalars().first()
    _attach_person_display_and_ids(obj, p1, p2)

    return obj


@router.put("/rfi-sources/{id}", response_model=RfiSourceRead, summary="Update RFI Source")
async def update_rfi_source(
    id: str = Path(..., description="Opaque rfi_source id"),
    payload: RfiSourceUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> RfiSourceRead:
    try:
        pk = decode_id("rfi_source", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="RFI Source not found")

    obj = await db.get(RfiSource, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="RFI Source not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.description is not None:
        obj.description = payload.description
    if payload.primary_id is not None:
        obj.primary_id = await _person_to_app_user_id(db, payload.primary_id)
    if payload.backup_id is not None:
        obj.backup_id = await _person_to_app_user_id(db, payload.backup_id)
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    # attach display fields for response
    p1 = None
    p2 = None
    if obj.primary_id is not None:
        p1 = (await db.execute(select(Person).where(Person.app_user_id == obj.primary_id))).scalars().first()
    if obj.backup_id is not None:
        p2 = (await db.execute(select(Person).where(Person.app_user_id == obj.backup_id))).scalars().first()
    _attach_person_display_and_ids(obj, p1, p2)

    return obj
