from typing import Optional
from datetime import date as _Date, time as _Time

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.subject import Subject
from app.db.models.ref_value import RefValue
from app.db.models.timeline import Timeline

from .case_utils import _decode_or_404, can_user_access_case
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

router = APIRouter()


@router.get("/{case_id}/timeline", summary="List timeline entries for a case")
async def list_timeline(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    # Join Subject for who display and RefValue for type
    type_ref = aliased(RefValue)
    q = (
        select(
            Timeline.id,
            Timeline.date,
            Timeline.time,
            Timeline.who_id,
            Timeline.where,
            Timeline.details,
            Timeline.rule_out,
            Timeline.type_id,
            Timeline.type_other,
            Timeline.comments,
            Timeline.questions,
            Subject.first_name,
            Subject.last_name,
            type_ref.name,
            type_ref.code,
        )
        .join(Subject, Subject.id == Timeline.who_id, isouter=True)
        .join(type_ref, type_ref.id == Timeline.type_id, isouter=True)
        .where(Timeline.case_id == int(case_db_id))
        .order_by(asc(Timeline.date), asc(Timeline.time), asc(Timeline.id))
    )

    rows = (await db.execute(q)).all()
    items = []
    for (
        tl_id,
        dt,
        tm,
        who_id,
        where,
        details,
        rule_out,
        type_id,
        type_other,
        comments,
        questions,
        first,
        last,
        type_name,
        type_code,
    ) in rows:
        items.append({
            "id": encode_id("timeline", int(tl_id)),
            "date": dt,
            "time": tm,
            "who_id": encode_id("subject", int(who_id)) if who_id is not None else None,
            "who_name": (f"{first or ''} {last or ''}".strip() if (first or last) else None),
            "where": where,
            "details": details,
            "rule_out": bool(rule_out) if rule_out is not None else False,
            "type_id": encode_id("ref_value", int(type_id)) if type_id is not None else None,
            "type_other": type_other,
            "type_name": type_name,
            "type_code": type_code,
            "comments": comments,
            "questions": questions,
        })

    return items


from pydantic import BaseModel

class TimelinePartial(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    who_id: Optional[str] = None
    where: Optional[str] = None
    details: Optional[str] = None
    rule_out: Optional[bool] = None
    type_id: Optional[str] = None
    type_other: Optional[str] = None
    comments: Optional[str] = None
    questions: Optional[str] = None


@router.patch("/{case_id}/timeline/{timeline_id}", summary="Update a timeline entry for a case")
async def update_timeline(
    case_id: str,
    timeline_id: str,
    payload: TimelinePartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        tl_db_id = decode_id("timeline", timeline_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Timeline entry not found")

    row = (await db.execute(select(Timeline).where(Timeline.id == int(tl_db_id), Timeline.case_id == int(case_db_id)))).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Timeline entry not found")

    def _parse_date(s: Optional[str]) -> Optional[_Date]:
        if not s:
            return None
        try:
            return _Date.fromisoformat(s)
        except Exception:
            return None

    def _parse_time(s: Optional[str]) -> Optional[_Time]:
        if not s:
            return None
        try:
            return _Time.fromisoformat(s)
        except Exception:
            return None

    def _dec_subject(oid: Optional[str]) -> Optional[int]:
        if not oid:
            return None
        try:
            return int(decode_id("subject", oid)) if not str(oid).isdigit() else int(oid)
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
    if "time" in fields_set:
        row.time = _parse_time(payload.time) or row.time
    if "who_id" in fields_set:
        row.who_id = _dec_subject(payload.who_id)
    if "where" in fields_set:
        row.where = payload.where
    if "details" in fields_set:
        row.details = payload.details
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False
    if "type_id" in fields_set:
        row.type_id = _dec_ref(payload.type_id, row.type_id)
    if "type_other" in fields_set:
        row.type_other = payload.type_other
    if "comments" in fields_set:
        row.comments = payload.comments
    if "questions" in fields_set:
        row.questions = payload.questions

    await db.commit()
    return {"ok": True}


@router.post("/{case_id}/timeline", summary="Create a timeline row for a case")
async def create_timeline(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    row = Timeline(
        case_id=int(case_db_id),
        date=_Date.today(),
        time=None,
        who_id=None,
        where=None,
        details=None,
        rule_out=False,
        type_id=None,
        type_other=None,
        comments=None,
        questions=None,
    )
    
    db.add(row)
    await db.commit()

    return {"ok": True}
