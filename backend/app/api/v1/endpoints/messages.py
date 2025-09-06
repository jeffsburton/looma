from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person
from app.db.models.message import Message
from app.db.models.message_person import MessagePerson
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case

router = APIRouter()


from pydantic import BaseModel as _BaseModel_MSG
from typing import Optional as _Optional_MSG, List as _List_MSG

class MessageCreate(_BaseModel_MSG):
    message: str
    reply_to_id: _Optional_MSG[str] = None

class MarkSeenRequest(_BaseModel_MSG):
    message_ids: _List_MSG[str]

class ReactionRequest(_BaseModel_MSG):
    reaction: _Optional_MSG[str] = None


@router.get("/{case_id}/messages", summary="List messages for a case")
async def list_case_messages(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    # Resolve current user's person id
    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    # Precompute current user's photo URL once
    me_has_pic = (await db.execute(select(Person.profile_pic.isnot(None)).where(Person.id == pid))).scalar() or False
    my_photo_url = f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=xs" if me_has_pic else "/images/pfp-generic.png"

    P = Person
    M = Message
    MP = MessagePerson
    M2 = aliased(M)

    q = (
        select(
            M.id,
            M.case_id,
            M.written_by_id,
            M.message,
            M.reply_to_id,
            M.created_at,
            M.updated_at,
            (P.first_name + sa.literal(" ") + P.last_name).label("writer_name"),
            P.profile_pic.isnot(None).label("writer_has_pic"),
            MP.id.isnot(None).label("seen"),
            MP.reaction.label("reaction"),
            M2.message.label("reply_to_text"),
        )
        .select_from(M)
        .join(P, P.id == M.written_by_id, isouter=True)
        .join(MP, sa.and_(MP.message_id == M.id, MP.person_id == pid), isouter=True)
        .join(M2, M2.id == M.reply_to_id, isouter=True)
        .where(M.case_id == pk)
        .order_by(sa.asc(M.created_at), sa.asc(M.id))
    )
    rows = (await db.execute(q)).all()

    items = []
    for r in rows:
        written_by_id = int(r.written_by_id) if r.written_by_id is not None else None
        is_mine = (written_by_id == int(pid)) if written_by_id is not None else False
        writer_photo_url = (
            f"/api/v1/media/pfp/person/{encode_id('person', int(written_by_id))}?s=xs" if getattr(r, "writer_has_pic", False) and written_by_id is not None else "/images/pfp-generic.png"
        )
        items.append({
            "id": int(r.id),
            "case_id": int(r.case_id),
            "written_by_id": written_by_id,
            "message": r.message,
            "reply_to_id": int(r.reply_to_id) if r.reply_to_id is not None else None,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "writer_name": getattr(r, "writer_name", None),
            "seen": bool(getattr(r, "seen", False)),
            "reaction": getattr(r, "reaction", None),
            "reply_to_text": getattr(r, "reply_to_text", None),
            "is_mine": bool(is_mine),
            "writer_photo_url": writer_photo_url,
            "my_photo_url": my_photo_url,
        })
    return items


@router.post("/{case_id}/messages", summary="Create a new message in a case")
async def create_case_message(
    case_id: str,
    payload: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    rid: _Optional_MSG[int] = None
    if payload.reply_to_id:
        try:
            rid = decode_id("message", payload.reply_to_id) if not str(payload.reply_to_id).isdigit() else int(payload.reply_to_id)
        except OpaqueIdError:
            rid = None

    msg = Message(case_id=pk, written_by_id=int(pid), message=payload.message, reply_to_id=rid)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    return {
        "id": int(msg.id),
        "case_id": int(msg.case_id),
        "written_by_id": int(msg.written_by_id) if msg.written_by_id is not None else None,
        "message": msg.message,
        "reply_to_id": int(msg.reply_to_id) if msg.reply_to_id is not None else None,
        "created_at": msg.created_at,
        "updated_at": msg.updated_at,
    }


@router.post("/{case_id}/messages/mark_seen", summary="Mark messages as seen for current user")
async def mark_messages_seen(
    case_id: str,
    payload: MarkSeenRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    # Decode message IDs and filter to those that belong to the case
    ids: _List_MSG[int] = []
    for mid in payload.message_ids or []:
        try:
            ids.append(decode_id("message", mid) if not str(mid).isdigit() else int(mid))
        except OpaqueIdError:
            continue

    if not ids:
        return {"updated": 0}

    # Only messages from this case
    valid_ids = (
        await db.execute(select(Message.id).where(Message.id.in_(ids), Message.case_id == pk))
    ).scalars().all()
    if not valid_ids:
        return {"updated": 0}

    # Find existing seen records
    existing = (
        await db.execute(select(MessagePerson.message_id).where(MessagePerson.person_id == pid, MessagePerson.message_id.in_(valid_ids)))
    ).scalars().all()
    existing_set = set(int(x) for x in existing)

    # Insert missing
    to_create = [int(x) for x in valid_ids if int(x) not in existing_set]
    for mid in to_create:
        db.add(MessagePerson(message_id=int(mid), person_id=int(pid)))

    if to_create:
        await db.commit()

    return {"updated": len(to_create)}


@router.post("/{case_id}/messages/{message_id}/reaction", summary="Set reaction emoji for current user on a message")
async def set_message_reaction(
    case_id: str,
    message_id: str,
    payload: ReactionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    try:
        mid = decode_id("message", message_id) if not str(message_id).isdigit() else int(message_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    # Ensure message belongs to the case
    owns = (await db.execute(select(Message.id).where(Message.id == mid, Message.case_id == pk))).scalar_one_or_none()
    if owns is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Upsert message_person for this (message, person)
    row = (
        await db.execute(select(MessagePerson).where(MessagePerson.message_id == mid, MessagePerson.person_id == pid))
    ).scalars().first()

    reaction_val = payload.reaction if (payload and hasattr(payload, 'reaction')) else None

    if row:
        row.reaction = reaction_val
    else:
        db.add(MessagePerson(message_id=mid, person_id=int(pid), reaction=reaction_val))

    await db.commit()

    return {"ok": True}


@router.get("/{case_id}/messages/unseen_count", summary="Get unseen message count for current user in a case")
async def unseen_message_count(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    pk = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, pk):
        raise HTTPException(status_code=404, detail="Case not found")

    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    M = Message
    MP = MessagePerson

    # Count messages in case that current person hasn't seen; exclude own messages
    subq = select(1).where(sa.and_(MP.message_id == M.id, MP.person_id == pid)).limit(1)
    q = select(sa.func.count()).where(sa.and_(M.case_id == pk, M.written_by_id != pid, sa.not_(sa.exists(subq))))

    count = (await db.execute(q)).scalar() or 0
    return {"count": int(count)}
