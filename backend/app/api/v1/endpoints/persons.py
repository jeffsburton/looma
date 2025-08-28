from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.person import Person
from app.schemas.person import PersonRead

# Simple authenticated listing for person selection widgets
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/persons", response_model=List[PersonRead], summary="List people")
async def list_persons(db: AsyncSession = Depends(get_db)) -> List[PersonRead]:
    result = await db.execute(select(Person))
    return list(result.scalars().all())
