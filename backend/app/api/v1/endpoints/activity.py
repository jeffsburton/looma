from typing import Optional
from datetime import date as Date

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.ref_value import RefValue
from app.db.models.person import Person
from app.db.models.person_case import PersonCase
from app.db.models.intel_activity import IntelActivity

from .case_utils import _decode_or_404, can_user_access_case
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

router = APIRouter()


@router.get("/{case_id}/activity", summary="List activity entries for a case")
async def list_activity(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    source_ref = aliased(RefValue)
    reported_to_ref = aliased(RefValue)

    q = (
        select(
            IntelActivity.id,
            IntelActivity.date,
            IntelActivity.entered_by_id,
            IntelActivity.what,
            IntelActivity.source_id,
            IntelActivity.source_other,
            IntelActivity.findings,
            IntelActivity.case_management,
            IntelActivity.reported_to,
            IntelActivity.reported_to_other,
            IntelActivity.on_eod_report,
            IntelActivity.rule_out,
            Person.first_name,
            Person.last_name,
            source_ref.name,
            source_ref.code,
            reported_to_ref.name,
            reported_to_ref.code,
        )
        .join(Person, Person.id == IntelActivity.entered_by_id, isouter=True)
        .join(source_ref, source_ref.id == IntelActivity.source_id, isouter=True)
        .join(reported_to_ref, reported_to_ref.id == IntelActivity.reported_to, isouter=True)
        .where(IntelActivity.case_id == int(case_db_id))
        .order_by(asc(IntelActivity.date), asc(IntelActivity.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        ia_id,
        dt,
        entered_by_id,
        what,
        source_id,
        source_other,
        findings,
        case_management,
        reported_to,
        reported_to_other,
        on_eod_report,
        rule_out,
        first,
        last,
        source_name,
        source_code,
        rep_to_name,
        rep_to_code,
    ) in rows:
        items.append({
            "id": encode_id("intel_activity", int(ia_id)),
            "date": dt,
            "entered_by_id": encode_id("person", int(entered_by_id)) if entered_by_id is not None else None,
            "entered_by_name": (f"{first or ''} {last or ''}".strip() if (first or last) else None),
            "what": what,
            "source_id": encode_id("ref_value", int(source_id)) if source_id is not None else None,
            "source_other": source_other,
            "findings": findings,
            "case_management": case_management,
            "reported_to": encode_id("ref_value", int(reported_to)) if reported_to is not None else None,
            "reported_to_other": reported_to_other,
            "on_eod_report": bool(on_eod_report) if on_eod_report is not None else False,
            "rule_out": bool(rule_out) if rule_out is not None else False,
            "source_name": source_name,
            "source_code": source_code,
            "reported_to_name": rep_to_name,
            "reported_to_code": rep_to_code,
        })

    return items


from pydantic import BaseModel

class IntelActivityPartial(BaseModel):
    date: Optional[str] = None
    what: Optional[str] = None
    source_id: Optional[str] = None
    source_other: Optional[str] = None
    findings: Optional[str] = None
    case_management: Optional[str] = None
    reported_to: Optional[str] = None
    reported_to_other: Optional[str] = None
    on_eod_report: Optional[bool] = None
    rule_out: Optional[bool] = None


@router.patch("/{case_id}/activity/{activity_id}", summary="Update an activity entry for a case")
async def update_activity(
    case_id: str,
    activity_id: str,
    payload: IntelActivityPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        ia_db_id = decode_id("intel_activity", activity_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Activity entry not found")

    row = (await db.execute(select(IntelActivity).where(IntelActivity.id == int(ia_db_id), IntelActivity.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Activity entry not found")

    def _parse_date(s: Optional[str]):
        if not s:
            return None
        try:
            return Date.fromisoformat(s)
        except Exception:
            return None

    def _dec_ref(oid: Optional[str], current_val: Optional[int]) -> Optional[int]:
        if oid is None:
            return current_val
        s = str(oid)
        if s == "":
            return None
        try:
            return int(decode_id("ref_value", s)) if not s.isdigit() else int(s)
        except Exception:
            return None

    fields_set = getattr(payload, "model_fields_set", set())

    if "date" in fields_set:
        row.date = _parse_date(payload.date) or row.date
    if "what" in fields_set:
        row.what = payload.what
    if "source_id" in fields_set:
        row.source_id = _dec_ref(payload.source_id, row.source_id)
    if "source_other" in fields_set:
        row.source_other = payload.source_other
    if "findings" in fields_set:
        row.findings = payload.findings
    if "case_management" in fields_set:
        row.case_management = payload.case_management
    if "reported_to" in fields_set:
        row.reported_to = _dec_ref(payload.reported_to, row.reported_to)
    if "reported_to_other" in fields_set:
        row.reported_to_other = payload.reported_to_other
    if "on_eod_report" in fields_set:
        row.on_eod_report = bool(payload.on_eod_report) if payload.on_eod_report is not None else False
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    return {"ok": True}


@router.post(
    "/{case_id}/activity",
    summary="Create an activity row for a case",
    dependencies=[Depends(require_permission("CONTACTS.MODIFY"))],
)
async def create_activity(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Pick an arbitrary person linked to the case to satisfy entered_by_id
    pc = (
        await db.execute(
            select(PersonCase.person_id).where(PersonCase.case_id == int(case_db_id)).order_by(asc(PersonCase.id)).limit(1)
        )
    ).scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=400, detail="No person linked to case to attribute entry")

    row = IntelActivity(
        case_id=int(case_db_id),
        entered_by_id=int(pc),
        date=Date.today(),
        what=None,
        source_id=None,
        source_other=None,
        findings=None,
        case_management=None,
        reported_to=None,
        reported_to_other=None,
        on_eod_report=False,
        rule_out=False,
    )
    db.add(row)
    await db.commit()

    return {"ok": True}
