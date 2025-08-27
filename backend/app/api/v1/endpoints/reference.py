from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.reference import StateRead, RefValueRead, RefValueCreate
from app.db.models.ref_value import RefValue
from app.db.models.ref_type import RefType

router = APIRouter()


@router.get("/states", response_model=List[StateRead], summary="List states")
async def list_states(db: AsyncSession = Depends(get_db)) -> List[StateRead]:
    # Return only RefValue entries where RefType.code == "STATE"
    stmt = (
        select(RefValue)
        .join(RefType, RefValue.ref_type_id == RefType.id)
        .where(RefType.code == "STATE")
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows


@router.get("/reference/{code}/values", response_model=List[RefValueRead], summary="List reference values for a type code")
async def list_ref_values(
    code: str = Path(..., description="ref_type.code to filter by"),
    db: AsyncSession = Depends(get_db),
) -> List[RefValueRead]:
    # Find ref_type id by code and then list values
    rt_result = await db.execute(select(RefType).where(RefType.code == code))
    ref_type = rt_result.scalars().first()
    if not ref_type:
        return []
    result = await db.execute(select(RefValue).where(RefValue.ref_type_id == ref_type.id))
    return result.scalars().all()


@router.post("/reference/{code}/values", response_model=RefValueRead, summary="Create reference value for a type code")
async def create_ref_value(
    code: str = Path(..., description="ref_type.code to add to"),
    payload: RefValueCreate = None,
    db: AsyncSession = Depends(get_db),
) -> RefValueRead:
    if payload is None or not payload.name or not payload.code:
        raise HTTPException(status_code=400, detail="name and code are required")

    rt_result = await db.execute(select(RefType).where(RefType.code == code))
    ref_type = rt_result.scalars().first()
    if not ref_type:
        raise HTTPException(status_code=404, detail="Reference type not found")

    obj = RefValue(
        name=payload.name,
        description=payload.description or "",
        code=payload.code,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
        num_value=payload.num_value,
        ref_type_id=ref_type.id,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()
    return obj
