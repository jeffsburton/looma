from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.organization import Organization
from app.schemas.organization import OrganizationRead

router = APIRouter()


@router.get("/organizations", response_model=List[OrganizationRead], summary="List organizations")
async def list_organizations(db: AsyncSession = Depends(get_db)) -> List[OrganizationRead]:
    result = await db.execute(select(Organization))
    rows = result.scalars().all()
    return rows
