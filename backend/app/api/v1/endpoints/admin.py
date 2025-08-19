from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models.qualification import Qualification
from app.schemas.qualification import QualificationRead, QualificationUpsert
from app.core.id_codec import decode_id, OpaqueIdError

router = APIRouter(prefix="/admin")


@router.get("/qualifications", response_model=List[QualificationRead], summary="List qualifications")
async def list_qualifications(db: AsyncSession = Depends(get_db)) -> List[QualificationRead]:
    result = await db.execute(select(Qualification))
    rows = result.scalars().all()
    return rows


@router.put(
    "/qualifications",
    response_model=List[QualificationRead],
    summary="Create or update qualifications (bulk upsert)",
)
async def upsert_qualifications(
    payload: List[QualificationUpsert],
    db: AsyncSession = Depends(get_db),
) -> List[QualificationRead]:
    out: list[Qualification] = []

    for item in payload:
        # Determine if this is update or create
        if item.id:
            try:
                pk = decode_id("qualification", item.id)
            except OpaqueIdError:
                raise HTTPException(status_code=404, detail="Qualification not found")

            obj = await db.get(Qualification, pk)
            if not obj:
                raise HTTPException(status_code=404, detail="Qualification not found")
            obj.name = item.name
            obj.code = item.code
            out.append(obj)
        else:
            obj = Qualification(name=item.name, code=item.code)
            db.add(obj)
            out.append(obj)

    # Persist and ensure PKs are available for newly created rows
    await db.flush()
    await db.commit()

    # Refresh to get updated timestamps
    for obj in out:
        await db.refresh(obj)

    return out
