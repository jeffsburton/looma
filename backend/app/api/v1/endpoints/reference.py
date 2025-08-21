from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.schemas.reference import StateRead

router = APIRouter()


@router.get("/states", response_model=List[StateRead], summary="List states")
async def list_states(db: AsyncSession = Depends(get_db)) -> List[StateRead]:
    result = await db.execute(select(RefValue))
    rows = result.scalars().all()
    return rows
