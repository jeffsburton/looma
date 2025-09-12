from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person
from app.db.models.person_case import PersonCase
from app.db.models.ref_value import RefValue
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case
from pydantic import BaseModel

router = APIRouter()


class PersonCaseCreate(BaseModel):
    person_id: str
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    notes: Optional[str] = None

from pydantic import BaseModel

@router.get("/{case_id}/persons", summary="List agency personnel (person_case rows) for a case")
async def list_case_persons(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    RelRV = aliased(RefValue)
    q = (
        select(
            PersonCase.id.label("pc_id"),
            PersonCase.relationship_id,
            RelRV.name.label("relationship_name"),
            RelRV.code.label("relationship_code"),
            PersonCase.relationship_other,
            PersonCase.notes,
            Person.id.label("person_id"),
            Person.first_name,
            Person.last_name,
            Person.phone,
            Person.email,
        )
        .join(Person, Person.id == PersonCase.person_id)
        .join(RelRV, RelRV.id == PersonCase.relationship_id, isouter=True)
        .where(PersonCase.case_id == int(case_db_id))
        .order_by(asc(Person.last_name), asc(Person.first_name))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        pc_id,
        rel_id,
        rel_name,
        rel_code,
        rel_other,
        notes,
        pid,
        first,
        last,
        phone,
        email,
    ) in rows:
        items.append({
            "id": encode_id("person_case", int(pc_id)),
            "raw_id": int(pc_id),
            "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
            "relationship_name": rel_name,
            "relationship_code": rel_code,
            "relationship_other": rel_other,
            "notes": notes,
            "person": {
                "id": encode_id("person", int(pid)),
                "first_name": first,
                "last_name": last,
                "phone": phone,
                "email": email,
                "photo_url": f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=xs" ,
            },
        })

    return items


@router.post(
    "/{case_id}/persons",
    summary="Create a person_case row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_case_person(
    case_id: str,
    payload: PersonCaseCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        person_db_id = decode_id("person", payload.person_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Person not found")

    person_exists = (await db.execute(select(Person.id).where(Person.id == int(person_db_id)))).scalar_one_or_none()
    if person_exists is None:
        raise HTTPException(status_code=404, detail="Person not found")

    exists_row = (await db.execute(select(PersonCase.id).where(
        PersonCase.case_id == int(case_db_id),
        PersonCase.person_id == int(person_db_id),
    ))).scalar_one_or_none()
    if exists_row is not None:
        return {"ok": True, "already_exists": True}

    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    row = PersonCase(
        case_id=int(case_db_id),
        person_id=int(person_db_id),
        relationship_id=_dec_ref(payload.relationship_id) if hasattr(payload, "relationship_id") else None,
        relationship_other=getattr(payload, "relationship_other", None),
        notes=getattr(payload, "notes", None),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


class PersonCasePartial(BaseModel):
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    notes: Optional[str] = None


@router.patch("/{case_id}/persons/{person_case_id}", summary="Update a person_case row for a case")
async def update_case_person(
    case_id: str,
    person_case_id: str,
    payload: PersonCasePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        pc_db_id = decode_id("person_case", person_case_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Person link not found")

    row = (await db.execute(select(PersonCase).where(PersonCase.id == int(pc_db_id), PersonCase.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Person link not found")

    def _dec_ref(oid: Optional[str]):
        if oid is None:
            return None
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "relationship_id" in fields_set:
        row.relationship_id = _dec_ref(payload.relationship_id)
    if "relationship_other" in fields_set:
        row.relationship_other = payload.relationship_other
    if "notes" in fields_set:
        row.notes = payload.notes

    await db.commit()
    return {"ok": True}
