from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.qualification import Qualification
from app.schemas.qualification import QualificationRead, QualificationUpsert
from app.core.id_codec import decode_id, OpaqueIdError


router = APIRouter(dependencies=[Depends(require_permission("QUALIFICATIONS"))])


@router.get("/qualifications", response_model=List[QualificationRead], summary="List Qualifications")
async def list_qualifications(db: AsyncSession = Depends(get_db)) -> List[QualificationRead]:
    result = await db.execute(select(Qualification))
    return result.scalars().all()


@router.post("/qualifications", response_model=QualificationRead, summary="Create Qualification")
async def create_qualification(payload: QualificationUpsert, db: AsyncSession = Depends(get_db)) -> QualificationRead:
    obj = Qualification(
        name=payload.name,
        description=payload.description,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()
    return obj


@router.put("/qualifications/{id}", response_model=QualificationRead, summary="Update Qualification")
async def update_qualification(
    id: str = Path(..., description="Opaque qualification id"),
    payload: QualificationUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> QualificationRead:
    try:
        pk = decode_id("qualification", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Qualification not found")

    obj = await db.get(Qualification, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Qualification not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.description is not None:
        obj.description = payload.description
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    return obj
