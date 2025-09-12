from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.subject import Subject
from app.db.models.subject_case import SubjectCase
from app.db.models.ref_value import RefValue
from app.db.models.case import Case
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case, case_number_or_id

router = APIRouter()

from pydantic import BaseModel

@router.get("/{case_id}/subjects", summary="List investigatory subjects (subject_case rows) for a case")
async def list_case_subjects(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize
    case_db_id = await case_number_or_id(db, current_user, case_id)

    RelRV = aliased(RefValue)
    q = (
        select(
            SubjectCase.id.label("sc_id"),
            SubjectCase.relationship_id,
            RelRV.name.label("relationship_name"),
            RelRV.code.label("relationship_code"),
            SubjectCase.relationship_other,
            SubjectCase.legal_guardian,
            SubjectCase.notes,
            SubjectCase.rule_out,
            Subject.id.label("subj_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.nicknames,
            Subject.phone,
            Subject.email,
            Subject.dangerous,
            Subject.danger,
        )
        .join(Subject, Subject.id == SubjectCase.subject_id)
        .join(RelRV, RelRV.id == SubjectCase.relationship_id, isouter=True)
        .where(SubjectCase.case_id == int(case_db_id))
        .order_by(asc(Subject.last_name), asc(Subject.first_name))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        sc_id,
        rel_id,
        rel_name,
        rel_code,
        rel_other,
        legal_guardian,
        notes,
        rule_out,
        subj_id,
        first,
        last,
        nicks,
        phone,
        email,
        dangerous,
        danger,
    ) in rows:
        items.append({
            "id": encode_id("subject_case", int(sc_id)),
            "raw_id": int(sc_id),
            "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
            "relationship_name": rel_name,
            "relationship_code": rel_code,
            "relationship_other": rel_other,
            "legal_guardian": bool(legal_guardian) if legal_guardian is not None else False,
            "notes": notes,
            "rule_out": bool(rule_out) if rule_out is not None else False,
            "subject": {
                "id": encode_id("subject", int(subj_id)),
                "raw_id": int(subj_id),
                "first_name": first,
                "last_name": last,
                "nicknames": nicks,
                "phone": phone,
                "email": email,
                "dangerous": bool(dangerous) if dangerous is not None else False,
                "danger": danger,
                "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(subj_id))}?s=xs" ,
            },
        })

    return items


@router.get("/{case_id}/subject/{subject_case_id}", summary="Get a single investigatory subject (subject_case row) for a case")
async def get_case_subject(
    case_id: str,
    subject_case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize: accept opaque id, raw id, or case_number
    case_db_id = await case_number_or_id(db, current_user, case_id)

    # Decode subject_case id (accept opaque or raw numeric)
    sc_db_id: Optional[int] = None
    try:
        sc_db_id = int(decode_id("subject_case", subject_case_id))
    except Exception:
        s = str(subject_case_id)
        if s.isdigit():
            sc_db_id = int(s)
        else:
            raise HTTPException(status_code=404, detail="Subject link not found")

    # Build the same SELECT as list_case_subjects, but filtered by row id and case id
    RelRV = aliased(RefValue)
    q = (
        select(
            SubjectCase.id.label("sc_id"),
            SubjectCase.relationship_id,
            RelRV.name.label("relationship_name"),
            RelRV.code.label("relationship_code"),
            SubjectCase.relationship_other,
            SubjectCase.legal_guardian,
            SubjectCase.notes,
            SubjectCase.rule_out,
            Subject.id.label("subj_id"),
            Subject.first_name,
            Subject.last_name,
            Subject.nicknames,
            Subject.phone,
            Subject.email,
            Subject.dangerous,
            Subject.danger,
        )
        .join(Subject, Subject.id == SubjectCase.subject_id)
        .join(RelRV, RelRV.id == SubjectCase.relationship_id, isouter=True)
        .where(
            SubjectCase.case_id == int(case_db_id),
            SubjectCase.id == int(sc_db_id),
        )
    )

    row = (await db.execute(q)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Subject link not found")

    (
        sc_id,
        rel_id,
        rel_name,
        rel_code,
        rel_other,
        legal_guardian,
        notes,
        rule_out,
        subj_id,
        first,
        last,
        nicks,
        phone,
        email,
        dangerous,
        danger,
    ) = row

    item = {
        "id": encode_id("subject_case", int(sc_id)),
        "raw_id": int(sc_id),
        "relationship_id": encode_id("ref_value", int(rel_id)) if rel_id is not None else None,
        "relationship_name": rel_name,
        "relationship_code": rel_code,
        "relationship_other": rel_other,
        "legal_guardian": bool(legal_guardian) if legal_guardian is not None else False,
        "notes": notes,
        "rule_out": bool(rule_out) if rule_out is not None else False,
        "subject": {
            "id": encode_id("subject", int(subj_id)),
            "raw_id": int(subj_id),
            "first_name": first,
            "last_name": last,
            "nicknames": nicks,
            "phone": phone,
            "email": email,
            "dangerous": bool(dangerous) if dangerous is not None else False,
            "danger": danger,
            "photo_url": f"/api/v1/media/pfp/subject/{encode_id('subject', int(subj_id))}?s=xs",
        },
    }

    return item


class SubjectCaseCreate(BaseModel):
    subject_id: str
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    legal_guardian: Optional[bool] = None
    notes: Optional[str] = None


@router.post(
    "/{case_id}/subjects",
    summary="Create a subject_case row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_case_subject(
    case_id: str,
    payload: SubjectCaseCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize: accept opaque id, raw id, or case_number
    case_db_id = await case_number_or_id(db, current_user, case_id)

    # Decode subject id
    try:
        subj_db_id = decode_id("subject", payload.subject_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Ensure subject exists
    subj = (await db.execute(select(Subject.id).where(Subject.id == int(subj_db_id)))).scalar_one_or_none()
    if subj is None:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Prevent duplicates (UniqueConstraint also exists)
    exists_row = (await db.execute(select(SubjectCase.id).where(
        SubjectCase.case_id == int(case_db_id),
        SubjectCase.subject_id == int(subj_db_id),
    ))).scalar_one_or_none()
    if exists_row is not None:
        # Treat as idempotent
        return {"ok": True, "already_exists": True}

    # Helper to decode optional ref_value id
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

    row = SubjectCase(
        case_id=int(case_db_id),
        subject_id=int(subj_db_id),
        relationship_id=_dec_ref(payload.relationship_id) if hasattr(payload, "relationship_id") else None,
        relationship_other=getattr(payload, "relationship_other", None),
        legal_guardian=bool(getattr(payload, "legal_guardian", False)),
        notes=getattr(payload, "notes", None),
    )
    db.add(row)
    await db.commit()

    return {"ok": True}


class SubjectCasePartial(BaseModel):
    subject_id: Optional[str] = None
    relationship_id: Optional[str] = None
    relationship_other: Optional[str] = None
    legal_guardian: Optional[bool] = None
    notes: Optional[str] = None
    rule_out: Optional[bool] = None


@router.patch("/{case_id}/subjects/{subject_case_id}", summary="Update a subject_case row for a case")
async def update_case_subject(
    case_id: str,
    subject_case_id: str,
    payload: SubjectCasePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Decode and authorize: accept opaque id, raw id, or case_number
    case_db_id = await case_number_or_id(db, current_user, case_id)

    try:
        sc_db_id = decode_id("subject_case", subject_case_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Subject link not found")

    # Load row and ensure it belongs to the case
    row = (await db.execute(select(SubjectCase).where(SubjectCase.id == int(sc_db_id), SubjectCase.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Subject link not found")

    # Helper to decode optional ref_value id
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

    # Update only fields explicitly provided in the payload
    fields_set = getattr(payload, "model_fields_set", set())

    # Optionally change linked subject
    if "subject_id" in fields_set:
        if payload.subject_id is None or str(payload.subject_id).strip() == "":
            raise HTTPException(status_code=400, detail="subject_id is required")
        try:
            new_subj_id = int(decode_id("subject", str(payload.subject_id))) if not str(payload.subject_id).isdigit() else int(str(payload.subject_id))
        except Exception:
            raise HTTPException(status_code=404, detail="Subject not found")
        # Check target subject exists
        subj_exists = (await db.execute(select(Subject.id).where(Subject.id == int(new_subj_id)))).scalar_one_or_none() is not None
        if not subj_exists:
            raise HTTPException(status_code=404, detail="Subject not found")
        # Enforce uniqueness per (case_id, subject_id)
        dup = (await db.execute(
            select(SubjectCase.id).where(
                SubjectCase.case_id == int(case_db_id),
                SubjectCase.subject_id == int(new_subj_id),
                SubjectCase.id != int(sc_db_id),
            )
        )).scalar_one_or_none()
        if dup is not None:
            raise HTTPException(status_code=400, detail="Subject already linked to case")
        row.subject_id = int(new_subj_id)

    if "relationship_id" in fields_set:
        row.relationship_id = _dec_ref(payload.relationship_id)
    if "relationship_other" in fields_set:
        row.relationship_other = payload.relationship_other
    if "legal_guardian" in fields_set:
        row.legal_guardian = bool(payload.legal_guardian) if payload.legal_guardian is not None else False
    if "notes" in fields_set:
        row.notes = payload.notes
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}
