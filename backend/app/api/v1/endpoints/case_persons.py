from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_user, require_permission
from app.db.models.case import Case
from app.db.models.organization import Organization
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person
from app.db.models.person_case import PersonCase
from app.db.models.ref_value import RefValue
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case, case_number_or_id
from pydantic import BaseModel

router = APIRouter()


@router.get("/{case_id}/person/{person_case_id}", summary="Get a single agency person (person_case row) for a case")
async def get_case_person(
    case_id: str,
    person_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = await case_number_or_id(db, current_user, case_id)


    # Decode person_case id (accept opaque or raw numeric)
    pc_db_id: Optional[int] = None
    try:
        pc_db_id = int(decode_id("person_case", person_case_id))
    except Exception:
        s = str(person_case_id)
        if s.isdigit():
            pc_db_id = int(s)
        else:
            raise HTTPException(status_code=404, detail="Person link not found")

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
            Organization.name.label("organization_name"),
        )
        .join(Person, Person.id == PersonCase.person_id)
        .join(RelRV, RelRV.id == PersonCase.relationship_id, isouter=True)
        .join(Organization, Organization.id == Person.organization_id, isouter=True)
        .where(
            PersonCase.case_id == int(case_db_id),
            PersonCase.id == int(pc_db_id),
        )
    )

    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Person link not found")

    (
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
        organization_name,
    ) = row

    item = {
        "id": encode_id("person_case", int(pc_id)),
        "raw_id": int(pc_id),
        "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
        "relationship_name": rel_name,
        "relationship_code": rel_code,
        "relationship_other": rel_other,
        "notes": notes,
        "person": {
            "id": encode_id("person", int(pid)),
            "raw_id": int(pid),
            "first_name": first,
            "last_name": last,
            "phone": phone,
            "email": email,
            "organization_name" : organization_name,
            "photo_url": f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=xs",
        },
    }

    return item


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
    # Decode and authorize
    case_db_id = await case_number_or_id(db, current_user, case_id)

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
            Organization.name.label("organization_name"),
        )
        .join(Person, Person.id == PersonCase.person_id)
        .join(RelRV, RelRV.id == PersonCase.relationship_id, isouter=True)
        .join(Organization, Organization.id == Person.organization_id, isouter=True)
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
        organization_name
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
                "organization_name" : organization_name,
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
    case_db_id = await case_number_or_id(db, current_user, case_id)

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
    person_id: Optional[str] = None
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
    case_db_id = await case_number_or_id(db, current_user, case_id)

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

    # Optionally change linked person
    if "person_id" in fields_set:
        if payload.person_id is None or str(payload.person_id).strip() == "":
            raise HTTPException(status_code=400, detail="person_id is required")
        try:
            new_person_id = int(decode_id("person", str(payload.person_id))) if not str(payload.person_id).isdigit() else int(str(payload.person_id))
        except Exception:
            raise HTTPException(status_code=404, detail="Person not found")
        # Check target person exists
        person_exists = (await db.execute(select(Person.id).where(Person.id == int(new_person_id)))).scalar_one_or_none() is not None
        if not person_exists:
            raise HTTPException(status_code=404, detail="Person not found")
        # Enforce uniqueness per (case_id, person_id)
        dup = (await db.execute(
            select(PersonCase.id).where(
                PersonCase.case_id == int(case_db_id),
                PersonCase.person_id == int(new_person_id),
                PersonCase.id != int(pc_db_id),
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(status_code=400, detail="Person already linked to case")
        row.person_id = int(new_person_id)

    if "relationship_id" in fields_set:
        row.relationship_id = _dec_ref(payload.relationship_id)
    if "relationship_other" in fields_set:
        row.relationship_other = payload.relationship_other
    if "notes" in fields_set:
        row.notes = payload.notes

    await db.commit()
    return {"ok": True}
