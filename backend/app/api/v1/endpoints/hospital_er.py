from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join

from app.api.dependencies import require_permission
from app.db.session import get_db
from app.db.models.hospital_er import HospitalEr
from app.db.models.ref_value import RefValue
from app.schemas.hospital_er import HospitalErRead, HospitalErUpsert
from app.core.id_codec import decode_id, OpaqueIdError


router = APIRouter(dependencies=[Depends(require_permission("HOSPITAL_ER"))])


@router.get("/hospital-ers", response_model=List[HospitalErRead], summary="List ER/Trauma Centers")
async def list_hospitals(db: AsyncSession = Depends(get_db)) -> List[HospitalErRead]:
    # Left join to bring in state code
    stmt = (
        select(HospitalEr, RefValue.code)
        .join(RefValue, HospitalEr.state_id == RefValue.id, isouter=True)
    )
    result = await db.execute(stmt)
    rows = []
    for er, state_code in result.all():
        # Attach transient attribute for serialization
        setattr(er, "state_code", state_code)
        rows.append(er)
    return rows


@router.post("/hospital-ers", response_model=HospitalErRead, summary="Create ER/Trauma Center")
async def create_hospital(payload: HospitalErUpsert, db: AsyncSession = Depends(get_db)) -> HospitalErRead:
    # state_id comes as opaque string per schema; decode to int
    try:
        state_pk = decode_id("ref_value", payload.state_id)
    except OpaqueIdError:
        raise HTTPException(status_code=400, detail="Invalid state_id")

    obj = HospitalEr(
        name=payload.name,
        address=payload.address,
        city=payload.city,
        state_id=state_pk,
        zip_code=payload.zip_code,
        phone=payload.phone,
        inactive=bool(payload.inactive) if payload.inactive is not None else False,
    )
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    await db.commit()
    # Fetch state code for response and attach to object
    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj


@router.put("/hospital-ers/{id}", response_model=HospitalErRead, summary="Update ER/Trauma Center")
async def update_hospital(
    id: str = Path(..., description="Opaque hospital_er id"),
    payload: HospitalErUpsert = None,
    db: AsyncSession = Depends(get_db),
) -> HospitalErRead:
    try:
        pk = decode_id("hospital_er", id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Hospital not found")

    obj = await db.get(HospitalEr, pk)
    if not obj:
        raise HTTPException(status_code=404, detail="Hospital not found")

    if payload.name is not None:
        obj.name = payload.name
    if payload.address is not None:
        obj.address = payload.address
    if payload.city is not None:
        obj.city = payload.city
    if payload.state_id is not None:
        try:
            obj.state_id = decode_id("ref_value", payload.state_id)
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid state_id")
    if payload.zip_code is not None:
        obj.zip_code = payload.zip_code
    if payload.phone is not None:
        obj.phone = payload.phone
    if payload.inactive is not None:
        obj.inactive = bool(payload.inactive)

    await db.flush()
    await db.refresh(obj)
    await db.commit()

    # Fetch state code for response and attach to object
    code_result = await db.execute(select(RefValue.code).where(RefValue.id == obj.state_id))
    obj.state_code = code_result.scalar_one_or_none()
    return obj
