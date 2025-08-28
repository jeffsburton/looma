from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.organization import Organization
from app.db.models.ref_value import RefValue
from app.schemas.organization import OrganizationRead, OrganizationUpsert
from app.core.id_codec import decode_id, OpaqueIdError

router = APIRouter(dependencies=[Depends(require_permission("ORGS"))])


@router.get("/organizations", response_model=List[OrganizationRead], summary="List organizations")
async def list_organizations(db: AsyncSession = Depends(get_db)) -> List[OrganizationRead]:
    # left join to include state code for UI convenience
    stmt = select(Organization, RefValue.code).join(RefValue, Organization.state_id == RefValue.id, isouter=True)
    result = await db.execute(stmt)
    rows: List[Organization] = []
    for org, state_code in result.all():
        setattr(org, "state_code", state_code)
        rows.append(org)
    return rows


@router.post("/organizations", response_model=OrganizationRead, summary="Create organization")
async def create_organization(payload: OrganizationUpsert, db: AsyncSession = Depends(get_db)) -> OrganizationRead:
    state_pk = None
    if payload.state_id is not None:
        try:
            state_pk = decode_id("ref_value", payload.state_id)
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid state_id")

    obj = Organization(name=payload.name, state_id=state_pk)
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()

    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj


@router.put("/organizations/{id}", response_model=OrganizationRead, summary="Update organization")
async def update_organization(
    id: str = Path(..., description="Opaque organization id"),
    payload: OrganizationUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> OrganizationRead:
    try:
        pk = decode_id("organization", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Organization not found")

    obj = await db.get(Organization, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Organization not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.state_id is not None:
        if payload.state_id == "":
            obj.state_id = None
        else:
            try:
                obj.state_id = decode_id("ref_value", payload.state_id)
            except OpaqueIdError:
                raise HTTPException(status_code=400, detail="Invalid state_id")

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj
