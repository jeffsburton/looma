from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.event import Event
from app.db.models.ref_value import RefValue
from app.schemas.event import EventRead, EventUpsert
from app.core.id_codec import decode_id, OpaqueIdError

router = APIRouter(dependencies=[Depends(require_permission("EVENTS"))])


@router.get("/events", response_model=List[EventRead], summary="List events")
async def list_events(db: AsyncSession = Depends(get_db)) -> List[EventRead]:
    # Left join to include state code for UI convenience
    stmt = select(Event, RefValue.code).join(RefValue, Event.state_id == RefValue.id, isouter=True)
    result = await db.execute(stmt)
    rows: List[Event] = []
    for ev, state_code in result.all():
        setattr(ev, "state_code", state_code)
        rows.append(ev)
    return rows


@router.post(
    "/events",
    response_model=EventRead,
    summary="Create event",
    dependencies=[Depends(require_permission("EVENTS.MODIFY"))],
)
async def create_event(payload: EventUpsert, db: AsyncSession = Depends(get_db)) -> EventRead:
    state_pk = None
    if payload.state_id is not None:
        try:
            state_pk = decode_id("ref_value", payload.state_id)
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid state_id")

    obj = Event(
        name=payload.name,
        city=(payload.city or ""),
        state_id=state_pk,
        start=payload.start,
        end=payload.end,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()

    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj


@router.put(
    "/events/{id}",
    response_model=EventRead,
    summary="Update event",
    dependencies=[Depends(require_permission("EVENTS.MODIFY"))],
)
async def update_event(
    id: str = Path(..., description="Opaque event id"),
    payload: EventUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> EventRead:
    try:
        pk = decode_id("event", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Event not found")

    obj = await db.get(Event, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Event not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.city is not None:
        obj.city = payload.city
    if payload.state_id is not None:
        if payload.state_id == "":
            obj.state_id = None
        else:
            try:
                obj.state_id = decode_id("ref_value", payload.state_id)
            except OpaqueIdError:
                raise HTTPException(status_code=400, detail="Invalid state_id")
    if payload.start is not None:
        obj.start = payload.start
    if payload.end is not None:
        obj.end = payload.end
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj
