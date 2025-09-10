from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Body, WebSocket, WebSocketDisconnect
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.api.dependencies import get_current_user, get_bearer_or_cookie_token
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person
from app.db.models.message import Message
from app.db.models.message_person import MessagePerson
from app.db.models.message_not_seen import MessageNotSeen
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.db.models.person_case import PersonCase
from app.db.models.app_user_role import AppUserRole
from app.db.models.role_permission import RolePermission
from app.db.models.permission import Permission
from app.core.id_codec import decode_id, OpaqueIdError, encode_id
from app.db.models.file import File as OtherFile
from app.services.s3 import get_download_link

from .case_utils import _decode_or_404, can_user_access_case
from app.schemas.message import MessageRead

router = APIRouter()


from pydantic import BaseModel as _BaseModel_MSG
from typing import Optional as _Optional_MSG, List as _List_MSG

class MessageCreate(_BaseModel_MSG):
    message: str
    reply_to_id: _Optional_MSG[str] = None
    file_id: _Optional_MSG[str] = None
    # Optional filtering/context fields. If provided when creating a message,
    # the corresponding foreign key on Message will be populated.
    filter_by_field_name: _Optional_MSG[str] = None  # one of: rfi_id, ops_plan_id, task_id
    filter_by_field_id: _Optional_MSG[str] = None    # encrypted id for corresponding entity

class MarkSeenRequest(_BaseModel_MSG):
    message_ids: _List_MSG[str]

class ReactionRequest(_BaseModel_MSG):
    reaction: _Optional_MSG[str] = None

class MarkSeenUpToResponse(_BaseModel_MSG):
    ok: bool = True
    cleared: int = 0

class ReactionGroup(_BaseModel_MSG):
    emoji: str
    count: int

class MessageReactionsRead(_BaseModel_MSG):
    message_id: str
    reactions: _List_MSG[ReactionGroup] = []
    my_reaction: _Optional_MSG[str] = None

async def _build_reaction_map(db: AsyncSession, mids: list[int]) -> dict[int, list[dict]]:
    """Aggregate reactions across all persons per message ids in `mids`.
    Returns a mapping: raw_message_id -> [{ emoji, count }, ...]
    """
    reaction_map: dict[int, list[dict]] = {}
    if not mids:
        return reaction_map
    MP = MessagePerson
    agg_q = (
        select(MP.message_id, MP.reaction, sa.func.count().label("cnt"))
        .where(MP.message_id.in_(mids), MP.reaction.is_not(None))
        .group_by(MP.message_id, MP.reaction)
    )
    agg_rows = (await db.execute(agg_q)).all()
    for ar in agg_rows:
        mid = int(ar.message_id)
        emoji = ar.reaction
        cnt = int(getattr(ar, "cnt", 0) or 0)
        if emoji is None or cnt <= 0:
            continue
        reaction_map.setdefault(mid, []).append({"emoji": emoji, "count": cnt})
    return reaction_map

# ------------------------------------------------------------
# Get messages for a case
# ------------------------------------------------------------
@router.get("/{case_id}/messages", summary="List messages for a case", response_model=List[MessageRead])
async def list_case_messages(
    case_id: str,
    filter_by_field_name: Optional[str] = None,
    filter_by_field_id: Optional[str] = None,
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
    MNS = MessageNotSeen

    # Optional filtering by related field id when provided
    conditions = [M.case_id == pk]
    if filter_by_field_name and filter_by_field_id:
        allowed = {"rfi_id": "rfi", "ops_plan_id": "ops_plan", "task_id": "task"}
        if filter_by_field_name not in allowed:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        try:
            raw_related_id = int(decode_id(allowed[filter_by_field_name], filter_by_field_id))
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_id")
        # Append condition on dynamic column
        try:
            column_attr = getattr(M, filter_by_field_name)
        except AttributeError:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        conditions.append(column_attr == raw_related_id)

    q = (
        select(
            M.id,
            M.case_id,
            M.written_by_id,
            M.message,
            M.reply_to_id,
            M.rule_out,
            M.task_id,
            M.created_at,
            M.updated_at,
            (P.first_name + sa.literal(" ") + P.last_name).label("writer_name"),
            P.profile_pic.isnot(None).label("writer_has_pic"),
            # seen = no corresponding MessageNotSeen row for this user
            (MNS.id.is_(None)).label("seen"),
            MP.reaction.label("reaction"),
            M2.message.label("reply_to_text"),
            OtherFile.id.label("file_id"),
            OtherFile.file_name.label("file_name"),
            OtherFile.mime_type.label("file_mime_type"),
            OtherFile.is_image.label("file_is_image"),
            OtherFile.is_video.label("file_is_video"),
        )
        .select_from(M)
        .join(P, P.id == M.written_by_id, isouter=True)
        .join(MP, sa.and_(MP.message_id == M.id, MP.person_id == pid), isouter=True)
        .join(M2, M2.id == M.reply_to_id, isouter=True)
        .join(MNS, sa.and_(MNS.message_id == M.id, MNS.person_id == pid), isouter=True)
        .join(OtherFile, OtherFile.id == M.file_id, isouter=True)
        .where(*conditions)
        .order_by(sa.asc(M.created_at), sa.asc(M.id))
    )
    rows = (await db.execute(q)).all()

    # Aggregate reactions across all persons per message
    mids = [int(r.id) for r in rows] if rows else []
    reaction_map: dict[int, list[dict]] = await _build_reaction_map(db, mids)

    items: list[MessageRead] = []
    for r in rows:
        written_by_id = int(r.written_by_id) if r.written_by_id is not None else None
        is_mine = (written_by_id == int(pid)) if written_by_id is not None else False
        writer_photo_url = (
            f"/api/v1/media/pfp/person/{encode_id('person', int(written_by_id))}?s=xs" if getattr(r, "writer_has_pic", False) and written_by_id is not None else "/images/pfp-generic.png"
        )
        items.append(
            MessageRead(
                id=int(r.id),
                case_id=int(r.case_id),
                written_by_id=written_by_id,
                message=r.message,
                reply_to_id=int(r.reply_to_id) if r.reply_to_id is not None else None,
                rule_out=bool(getattr(r, "rule_out", False)),
                task_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
                task_raw_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
                file_id=(int(getattr(r, "file_id")) if getattr(r, "file_id", None) is not None else None),
                file_name=(getattr(r, "file_name", None)),
                file_mime_type=(getattr(r, "file_mime_type", None)),
                file_is_image=bool(getattr(r, "file_is_image", False)) if getattr(r, "file_id", None) is not None else None,
                file_is_video=bool(getattr(r, "file_is_video", False)) if getattr(r, "file_id", None) is not None else None,
                file_url=(get_download_link("file", int(getattr(r, "file_id")), file_type=(getattr(r, "file_mime_type", None) or None), thumbnail=False, attachment_filename=(getattr(r, "file_name", None) or "download")) if getattr(r, "file_id", None) is not None else None),
                file_thumb=(get_download_link("file", int(getattr(r, "file_id")), file_type=None, thumbnail=True) if (getattr(r, "file_id", None) is not None and (bool(getattr(r, "file_is_image", False)) or bool(getattr(r, "file_is_video", False)))) else None),
                created_at=r.created_at,
                updated_at=r.updated_at,
                writer_name=getattr(r, "writer_name", None),
                seen=bool(getattr(r, "seen", False)),
                reaction=getattr(r, "reaction", None),
                reactions=reaction_map.get(int(r.id), []),
                reply_to_text=getattr(r, "reply_to_text", None),
                is_mine=bool(is_mine),
                writer_photo_url=writer_photo_url,
                my_photo_url=my_photo_url,
            )
        )
    return items

# ------------------------------------------------------------
# Create a new message
# ------------------------------------------------------------
@router.post("/{case_id}/messages", summary="Create a new message in a case", response_model=MessageRead)
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
            rid = decode_id("message", payload.reply_to_id)
        except OpaqueIdError:
            rid = None

    fid: _Optional_MSG[int] = None
    if getattr(payload, 'file_id', None):
        try:
            fid = decode_id("file", payload.file_id)
        except OpaqueIdError:
            try:
                fid = int(payload.file_id)
            except Exception:
                fid = None

    # Apply optional related field (rfi_id / ops_plan_id / task_id) if provided
    extra_kwargs = {}
    fbfn = getattr(payload, 'filter_by_field_name', None)
    fbfid = getattr(payload, 'filter_by_field_id', None)
    if fbfn and fbfid:
        allowed = {"rfi_id": "rfi", "ops_plan_id": "ops_plan", "task_id": "task"}
        if fbfn not in allowed:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        try:
            raw_related_id = int(decode_id(allowed[fbfn], fbfid))
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_id")
        # Ensure the Message model actually has this attribute
        if not hasattr(Message, fbfn):
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        extra_kwargs[fbfn] = raw_related_id

    msg = Message(case_id=pk, written_by_id=int(pid), message=payload.message, reply_to_id=rid, file_id=fid, **extra_kwargs)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    # Insert MessageNotSeen rows for all viewers of this case except the author
    try:
        case_pk = int(msg.case_id)
        author_pid = int(pid)

        # Cleanup: remove any stale MessageNotSeen entries older than 2 days (global)
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=2)
            await db.execute(sa.delete(MessageNotSeen).where(MessageNotSeen.created_at < cutoff))
            await db.commit()
        except Exception:
            # Ignore cleanup errors; do not block message creation
            try:
                await db.rollback()
            except Exception:
                pass

        # Persons via team membership on teams linked to case
        PT = PersonTeam
        TC = TeamCase
        team_rows = (
            await db.execute(
                select(sa.distinct(PT.person_id))
                .select_from(PT)
                .join(TC, TC.team_id == PT.team_id)
                .where(TC.case_id == case_pk)
            )
        ).scalars().all()

        # Persons directly linked to case
        PC = PersonCase
        direct_rows = (
            await db.execute(
                select(sa.distinct(PC.person_id)).where(PC.case_id == case_pk)
            )
        ).scalars().all()

        # Persons whose linked user has CASES.ALL_CASES permission
        P = Person
        AUR = AppUserRole
        RP = RolePermission
        Perm = Permission
        admin_rows = (
            await db.execute(
                select(sa.distinct(P.id))
                .select_from(P)
                .join(AUR, AUR.app_user_id == P.app_user_id)
                .join(RP, RP.role_id == AUR.role_id)
                .join(Perm, Perm.id == RP.permission_id)
                .where(Perm.code == "CASES.ALL_CASES")
            )
        ).scalars().all()

        person_ids = {int(x) for x in (team_rows or [])}
        person_ids.update(int(x) for x in (direct_rows or []))
        person_ids.update(int(x) for x in (admin_rows or []))
        # Exclude the author themselves
        person_ids.discard(author_pid)

        if person_ids:
            # Prepare objects; rely on unique constraint to avoid dups if concurrent
            db.add_all([MessageNotSeen(message_id=int(msg.id), person_id=pid_val) for pid_val in person_ids])
            await db.commit()
    except Exception:
        # Best-effort: do not fail message creation if notification staging fails
        try:
            await db.rollback()
        except Exception:
            pass

    # Build publish payload matching list_case_messages shape (per-connection fields added in manager)
    # Fetch writer name and photo flags, plus reply_to_text
    writer_name = None
    writer_has_pic = False
    writer_photo_url = "/images/pfp-generic.png"
    reply_to_text = None

    # Query writer person details
    P = Person
    row = (await db.execute(select(P.first_name, P.last_name, P.profile_pic.isnot(None)).where(P.id == msg.written_by_id))).first()
    if row:
        fn, ln, has_pic = row
        parts = [p for p in [fn, ln] if p]
        writer_name = " ".join(parts) if parts else None
        writer_has_pic = bool(has_pic)
        if writer_has_pic and msg.written_by_id is not None:
            writer_photo_url = f"/api/v1/media/pfp/person/{encode_id('person', int(msg.written_by_id))}?s=xs"

    # Query reply_to text if any
    if msg.reply_to_id is not None:
        reply_to_text = (await db.execute(select(Message.message).where(Message.id == msg.reply_to_id))).scalar_one_or_none()

    # Build response model (also used for websocket payload)
    _fid = int(msg.file_id or 0) if getattr(msg, 'file_id', None) else 0
    _fname = None
    _fmime = None
    _fimg = None
    _fvid = None
    if _fid:
        try:
            frow = (
                await db.execute(
                    select(OtherFile.file_name, OtherFile.mime_type, OtherFile.is_image, OtherFile.is_video).where(OtherFile.id == _fid)
                )
            ).first()
            if frow:
                _fname, _fmime, _fimg, _fvid = frow
                _fimg = bool(_fimg)
                _fvid = bool(_fvid)
        except Exception:
            _fname = _fname or None
    _furl = get_download_link("file", _fid, file_type=_fmime or None, thumbnail=False, attachment_filename=_fname or "download") if _fid else None
    _fthumb = (get_download_link("file", _fid, file_type=None, thumbnail=True) if _fid and (_fimg or _fvid) else None)

    msg_model = MessageRead(
        id=int(msg.id),
        case_id=int(msg.case_id),
        written_by_id=int(msg.written_by_id) if msg.written_by_id is not None else None,
        message=msg.message,
        reply_to_id=int(msg.reply_to_id) if msg.reply_to_id is not None else None,
        rule_out=bool(getattr(msg, "rule_out", False)),
        task_id=(int(getattr(msg, "task_id")) if getattr(msg, "task_id", None) is not None else None),
        task_raw_id=(int(getattr(msg, "task_id")) if getattr(msg, "task_id", None) is not None else None),
        file_id=(_fid or None),
        file_name=_fname,
        file_mime_type=_fmime,
        file_is_image=_fimg,
        file_is_video=_fvid,
        file_url=_furl,
        file_thumb=_fthumb,
        created_at=msg.created_at,
        updated_at=msg.updated_at,
        writer_name=writer_name,
        reaction=None,
        reactions=[],
        reply_to_text=reply_to_text,
        is_mine=True,  # author sees their own pushed message as mine
        writer_photo_url=writer_photo_url,
        my_photo_url=None,  # filled per-connection in ws manager
    )

    # Publish to subscribers of this case (per-connection fields will be added by manager)
    try:
        ws_payload = msg_model.model_dump(mode="json")
        ws_payload["author_person_id"] = int(pid)
        await _ws_manager.publish_count_change(int(msg.case_id))
    except Exception:
        # Do not fail the request if broadcasting fails
        pass

    # Return encrypted payload
    return msg_model


# ------------------------------------------------------------
# Add a reaction to a message
# ------------------------------------------------------------
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
        mid = decode_id("message", message_id)
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

    # Broadcast unified message change event (covers reaction updates)
    try:
        await _ws_manager.publish_message_change(pk, mid)
    except Exception:
        pass

    return {"ok": True}

# ------------------------------------------------------------
# Get grouped reactions for a single message
# ------------------------------------------------------------
@router.get("/{case_id}/messages/{message_id}/reactions", summary="Get grouped reactions for a message", response_model=MessageReactionsRead)
async def get_message_reactions(
    case_id: str,
    message_id: str,
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
        mid = int(decode_id("message", message_id))
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    # Ensure message belongs to the case
    owns = (await db.execute(select(Message.id).where(Message.id == mid, Message.case_id == pk))).scalar_one_or_none()
    if owns is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Grouped reactions
    reaction_map = await _build_reaction_map(db, [mid])
    groups = reaction_map.get(int(mid), [])

    # Current user's reaction
    my_reaction = (
        await db.execute(
            select(MessagePerson.reaction).where(MessagePerson.message_id == mid, MessagePerson.person_id == pid)
        )
    ).scalar_one_or_none()

    enc_mid = encode_id("message", int(mid))
    return MessageReactionsRead(
        message_id=enc_mid,
        reactions=[ReactionGroup(**g) for g in groups],
        my_reaction=my_reaction,
    )


# ------------------------------------------------------------
# Get a single message (enriched) matching list_case_messages shape
# ------------------------------------------------------------
@router.get("/{case_id}/messages/{message_id}", summary="Get a single message", response_model=MessageRead)
async def get_case_message(
    case_id: str,
    message_id: str,
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

    try:
        mid = int(decode_id("message", message_id))
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    # Ensure message belongs to the case
    owns = (await db.execute(select(Message.id).where(Message.id == mid, Message.case_id == pk))).scalar_one_or_none()
    if owns is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Precompute current user's photo URL once
    me_has_pic = (await db.execute(select(Person.profile_pic.isnot(None)).where(Person.id == pid))).scalar() or False
    my_photo_url = f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=xs" if me_has_pic else "/images/pfp-generic.png"

    P = Person
    M = Message
    MP = MessagePerson
    M2 = aliased(M)
    MNS = MessageNotSeen

    q = (
        select(
            M.id,
            M.case_id,
            M.written_by_id,
            M.message,
            M.reply_to_id,
            M.rule_out,
            M.created_at,
            M.updated_at,
            (P.first_name + sa.literal(" ") + P.last_name).label("writer_name"),
            P.profile_pic.isnot(None).label("writer_has_pic"),
            (MNS.id.is_(None)).label("seen"),
            MP.reaction.label("reaction"),
            M2.message.label("reply_to_text"),
            OtherFile.id.label("file_id"),
            OtherFile.file_name.label("file_name"),
            OtherFile.mime_type.label("file_mime_type"),
            OtherFile.is_image.label("file_is_image"),
            OtherFile.is_video.label("file_is_video"),
        )
        .select_from(M)
        .join(P, P.id == M.written_by_id, isouter=True)
        .join(MP, sa.and_(MP.message_id == M.id, MP.person_id == pid), isouter=True)
        .join(M2, M2.id == M.reply_to_id, isouter=True)
        .join(MNS, sa.and_(MNS.message_id == M.id, MNS.person_id == pid), isouter=True)
        .join(OtherFile, OtherFile.id == M.file_id, isouter=True)
        .where(M.case_id == pk, M.id == mid)
    )
    r = (await db.execute(q)).first()
    if not r:
        raise HTTPException(status_code=404, detail="Message not found")

    # Aggregate reactions for this message
    reaction_map: dict[int, list[dict]] = await _build_reaction_map(db, [mid])

    written_by_id = int(r.written_by_id) if r.written_by_id is not None else None
    is_mine = (written_by_id == int(pid)) if written_by_id is not None else False
    writer_photo_url = (
        f"/api/v1/media/pfp/person/{encode_id('person', int(written_by_id))}?s=xs" if getattr(r, "writer_has_pic", False) and written_by_id is not None else "/images/pfp-generic.png"
    )

    _fid = int(getattr(r, 'file_id') or 0) if getattr(r, 'file_id', None) is not None else 0
    _fname = getattr(r, 'file_name', None)
    _fmime = getattr(r, 'file_mime_type', None)
    _fimg = bool(getattr(r, 'file_is_image', False)) if _fid else None
    _fvid = bool(getattr(r, 'file_is_video', False)) if _fid else None
    _furl = get_download_link("file", int(_fid), file_type=(_fmime or None), thumbnail=False, attachment_filename=(_fname or "download")) if _fid else None
    _fthumb = (get_download_link("file", int(_fid), file_type=None, thumbnail=True) if _fid and (_fimg or _fvid) else None)

    return MessageRead(
        id=int(r.id),
        case_id=int(r.case_id),
        written_by_id=written_by_id,
        message=r.message,
        reply_to_id=int(r.reply_to_id) if r.reply_to_id is not None else None,
        rule_out=bool(getattr(r, "rule_out", False)),
        task_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
        task_raw_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
        file_id=(_fid or None),
        file_name=_fname,
        file_mime_type=_fmime,
        file_is_image=_fimg,
        file_is_video=_fvid,
        file_url=_furl,
        file_thumb=_fthumb,
        created_at=r.created_at,
        updated_at=r.updated_at,
        writer_name=getattr(r, "writer_name", None),
        seen=bool(getattr(r, "seen", False)),
        reaction=getattr(r, "reaction", None),
        reactions=reaction_map.get(int(r.id), []),
        reply_to_text=getattr(r, "reply_to_text", None),
        is_mine=bool(is_mine),
        writer_photo_url=writer_photo_url,
        my_photo_url=my_photo_url,
    )


# ------------------------------------------------------------
# Update a message (rule_out only)
# ------------------------------------------------------------
from pydantic import BaseModel as _BM_Partial
class MessagePartial(_BM_Partial):
    rule_out: _Optional_MSG[bool] = None

@router.patch("/{case_id}/messages/{message_id}", summary="Update a message (author only)")
async def update_message(
    case_id: str,
    message_id: str,
    payload: MessagePartial = Body(...),
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

    try:
        mid = int(decode_id("message", message_id))
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    row = (await db.execute(select(Message).where(Message.id == mid, Message.case_id == pk))).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Only the author can update
    if int(row.written_by_id or 0) != int(pid):
        raise HTTPException(status_code=403, detail="Not allowed")

    fields_set = getattr(payload, "model_fields_set", set())
    if "rule_out" in fields_set:
        row.rule_out = bool(payload.rule_out) if payload.rule_out is not None else False

    await db.commit()
    # Broadcast unified message change (e.g., rule_out toggled)
    try:
        await _ws_manager.publish_message_change(pk, mid)
    except Exception:
        pass
    return {"ok": True, "rule_out": bool(row.rule_out)}


# ------------------------------------------------------------
# Delete a message (author within 1 hour)
# ------------------------------------------------------------
@router.delete("/{case_id}/messages/{message_id}", summary="Delete a message (author within 1 hour)")
async def delete_message(
    case_id: str,
    message_id: str,
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

    try:
        mid = int(decode_id("message", message_id))
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    row = (await db.execute(select(Message).where(Message.id == mid, Message.case_id == pk))).scalars().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Only the author can delete
    if int(row.written_by_id or 0) != int(pid):
        raise HTTPException(status_code=403, detail="Not allowed")

    # Only within 1 hour of creation
    try:
        now = datetime.now(timezone.utc)
    except Exception:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
    created = row.created_at
    if created is None:
        raise HTTPException(status_code=400, detail="Invalid message timestamp")
    # Normalize timezone-awareness
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    if (now - created) > timedelta(hours=1):
        raise HTTPException(status_code=403, detail="Delete window has expired")

    # Proceed to delete; rely on ON DELETE constraints for related rows
    await db.delete(row)
    await db.commit()

    # Broadcast both: the message changed (deleted) and counts may have changed
    try:
        await _ws_manager.publish_message_change(pk, mid)
    except Exception:
        pass
    try:
        await _ws_manager.publish_count_change(int(pk))
    except Exception:
        pass

    return {"ok": True}

# ------------------------------------------------------------
# get new messages for a case
# ------------------------------------------------------------
@router.get("/messages/new_messages/case/{case_id}", summary="List new (unseen) messages for a case for the current user", response_model=List[MessageRead])
@router.get("/cases/messages/new_messages/case/{case_id}", include_in_schema=False, response_model=List[MessageRead])
async def list_new_case_messages(
    case_id: str,
    filter_by_field_name: Optional[str] = None,
    filter_by_field_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """Return messages for the given case that are currently marked as not seen
    by the current user (i.e., there exists a message_not_seen record for the
    message and this person). The payload shape matches list_case_messages.
    """
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
    MNS = MessageNotSeen

    # Optional filtering by related field id when provided
    conditions = [M.case_id == pk]
    if filter_by_field_name and filter_by_field_id:
        allowed = {"rfi_id": "rfi", "ops_plan_id": "ops_plan", "task_id": "task"}
        if filter_by_field_name not in allowed:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        try:
            raw_related_id = int(decode_id(allowed[filter_by_field_name], filter_by_field_id))
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_id")
        try:
            column_attr = getattr(M, filter_by_field_name)
        except AttributeError:
            raise HTTPException(status_code=400, detail="Invalid filter_by_field_name")
        conditions.append(column_attr == raw_related_id)

    q = (
        select(
            M.id,
            M.case_id,
            M.written_by_id,
            M.message,
            M.reply_to_id,
            M.rule_out,
            M.task_id,
            M.created_at,
            M.updated_at,
            (P.first_name + sa.literal(" ") + P.last_name).label("writer_name"),
            P.profile_pic.isnot(None).label("writer_has_pic"),
            # seen = no corresponding MessageNotSeen row (but here we INNER JOIN MNS, so this is always False)
            (MNS.id.is_(None)).label("seen"),
            MP.reaction.label("reaction"),
            M2.message.label("reply_to_text"),
            OtherFile.id.label("file_id"),
            OtherFile.file_name.label("file_name"),
            OtherFile.mime_type.label("file_mime_type"),
            OtherFile.is_image.label("file_is_image"),
            OtherFile.is_video.label("file_is_video"),
        )
        .select_from(M)
        .join(P, P.id == M.written_by_id, isouter=True)
        .join(MP, sa.and_(MP.message_id == M.id, MP.person_id == pid), isouter=True)
        .join(M2, M2.id == M.reply_to_id, isouter=True)
        .join(MNS, sa.and_(MNS.message_id == M.id, MNS.person_id == pid))
        .join(OtherFile, OtherFile.id == M.file_id, isouter=True)
        .where(*conditions)
        .order_by(sa.asc(M.created_at), sa.asc(M.id))
    )

    rows = (await db.execute(q)).all()

    # Aggregate reactions across all persons per message
    mids = [int(r.id) for r in rows] if rows else []
    reaction_map: dict[int, list[dict]] = await _build_reaction_map(db, mids)

    items: list[MessageRead] = []
    for r in rows:
        written_by_id = int(r.written_by_id) if r.written_by_id is not None else None
        is_mine = (written_by_id == int(pid)) if written_by_id is not None else False
        writer_photo_url = (
            f"/api/v1/media/pfp/person/{encode_id('person', int(written_by_id))}?s=xs" if getattr(r, "writer_has_pic", False) and written_by_id is not None else "/images/pfp-generic.png"
        )
        _fid = int(getattr(r, 'file_id') or 0) if getattr(r, 'file_id', None) is not None else 0
        _fname = getattr(r, 'file_name', None)
        _fmime = getattr(r, 'file_mime_type', None)
        _fimg = bool(getattr(r, 'file_is_image', False)) if _fid else None
        _fvid = bool(getattr(r, 'file_is_video', False)) if _fid else None
        _furl = get_download_link("file", int(_fid), file_type=(_fmime or None), thumbnail=False, attachment_filename=(_fname or "download")) if _fid else None
        _fthumb = (get_download_link("file", int(_fid), file_type=None, thumbnail=True) if _fid and (_fimg or _fvid) else None)
        items.append(
            MessageRead(
                id=int(r.id),
                case_id=int(r.case_id),
                written_by_id=written_by_id,
                message=r.message,
                reply_to_id=int(r.reply_to_id) if r.reply_to_id is not None else None,
                rule_out=bool(getattr(r, "rule_out", False)),
                task_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
                task_raw_id=(int(getattr(r, "task_id")) if getattr(r, "task_id", None) is not None else None),
                file_id=(_fid or None),
                file_name=_fname,
                file_mime_type=_fmime,
                file_is_image=_fimg,
                file_is_video=_fvid,
                file_url=_furl,
                file_thumb=_fthumb,
                created_at=r.created_at,
                updated_at=r.updated_at,
                writer_name=getattr(r, "writer_name", None),
                seen=bool(getattr(r, "seen", False)),
                reaction=getattr(r, "reaction", None),
                reactions=reaction_map.get(int(r.id), []),
                reply_to_text=getattr(r, "reply_to_text", None),
                is_mine=bool(is_mine),
                writer_photo_url=writer_photo_url,
                my_photo_url=my_photo_url,
            )
        )
    return items


# ------------------------------------------------------------
# Delete message_not_seen records
# ------------------------------------------------------------
@router.post("/{case_id}/messages/mark_seen_up_to/{message_id}", summary="Mark messages as seen up to the given message id (inclusive) for current user", response_model=MarkSeenUpToResponse)
async def mark_messages_seen_up_to(
    case_id: str,
    message_id: str,
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

    # Decode message id and ensure the message belongs to this case
    try:
        mid = int(decode_id("message", message_id))
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Message not found")

    owns = (await db.execute(select(Message.id).where(Message.id == mid, Message.case_id == pk))).scalar_one_or_none()
    if owns is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Count how many unseen rows would be cleared
    M = Message
    MNS = MessageNotSeen
    count_q = (
        select(sa.func.count())
        .select_from(MNS)
        .join(M, M.id == MNS.message_id)
        .where(MNS.person_id == pid, M.case_id == pk, M.id <= mid)
    )
    to_clear = int((await db.execute(count_q)).scalar() or 0)

    if to_clear:
        # Delete matching rows
        del_stmt = (
            sa.delete(MNS)
            .where(MNS.person_id == pid)
            .where(MNS.message_id.in_(select(M.id).where(M.case_id == pk, M.id <= mid)))
        )
        await db.execute(del_stmt)
        await db.commit()
        try:
            await _ws_manager.publish_count_change(int(pk))
        except Exception:

            pass

    return MarkSeenUpToResponse(ok=True, cleared=to_clear)




# ------------------------------------------------------------
# Standalone function: get unseen message counts for a user across all related cases
# Not a FastAPI route; accepts encrypted user id and session id, manages its own DB session
# ------------------------------------------------------------
async def unseen_counts_all_cases(encrypted_user_id: str, session_id: str) -> dict[str, int]:
    from app.core.id_codec import set_current_session, reset_current_session, decode_id, encode_id, OpaqueIdError
    from app.db.session import async_session_maker

    # Establish id_codec session context so decode_id/encode_id work
    ctx_token = set_current_session(session_id)
    try:
        # Decrypt the provided app_user id
        try:
            user_id = int(decode_id("app_user", encrypted_user_id))
        except OpaqueIdError:
            # Propagate a clear error for caller
            raise OpaqueIdError("Invalid encrypted user id or session context")

        async with async_session_maker() as db:
            # Resolve person's id linked to the user
            pid = (await db.execute(select(Person.id).where(Person.app_user_id == user_id))).scalar_one_or_none()
            if pid is None:
                # No linked person; treat as invalid usage
                raise ValueError("User is not linked to a person")

            M = Message
            MNS = MessageNotSeen

            # Single grouped query: by case and mutually exclusive dimension ids
            q = (
                select(
                    M.case_id.label("case_id"),
                    M.rfi_id.label("rfi_id"),
                    M.ops_plan_id.label("ops_plan_id"),
                    M.task_id.label("task_id"),
                    sa.func.count().label("cnt"),
                )
                .select_from(MNS)
                .join(M, M.id == MNS.message_id)
                .where(MNS.person_id == pid)
                .group_by(M.case_id, M.rfi_id, M.ops_plan_id, M.task_id)
            )

            # Get the SQL
            #sql = str(q.compile(compile_kwargs={"literal_binds": True}))
            #print(sql)

            rows = (await db.execute(q)).all()

            # Build flat JSON object with dynamic keys per specification
            result: dict[str, int] = {
                "count": 0,
                "count_rfis": 0,
                "count_ops_plans": 0,
                "count_tasks": 0,
            }

            # Helpers to increment counts safely
            def inc(key: str, amount: int) -> None:
                result[key] = int(result.get(key, 0)) + int(amount)

            for r in rows:
                cnt = int(getattr(r, "cnt", 0) or 0)
                if cnt <= 0:
                    continue

                # Global total
                inc("count", cnt)

                # Case-level totals
                case_id_raw = int(r.case_id)
                case_id_enc = encode_id("case", case_id_raw)
                inc(f"count_{case_id_enc}", cnt)

                # Dimension-specific handling (mutually exclusive)
                rid = r.rfi_id
                oid = r.ops_plan_id
                tid = r.task_id

                if rid is not None:
                    # Global category total
                    inc("count_rfis", cnt)
                    # Per-case category total
                    inc(f"count_rfis_{case_id_enc}", cnt)
                    # Per-entity within case
                    rfi_enc = encode_id("rfi", int(rid))
                    inc(f"count_rfis_{case_id_enc}_{rfi_enc}", cnt)
                elif oid is not None:
                    inc("count_ops_plans", cnt)
                    inc(f"count_ops_plans_{case_id_enc}", cnt)
                    ops_plan_enc = encode_id("ops_plan", int(oid))
                    inc(f"count_ops_plans_{case_id_enc}_{ops_plan_enc}", cnt)
                elif tid is not None:
                    inc("count_tasks", cnt)
                    inc(f"count_tasks_{case_id_enc}", cnt)
                    task_enc = encode_id("task", int(tid))
                    inc(f"count_tasks_{case_id_enc}_{task_enc}", cnt)
                else:
                    # Messages not tied to rfi/ops_plan/task are counted globally and per-case already
                    pass

            return result
    finally:
        try:
            reset_current_session(ctx_token)
        except Exception:
            pass


# ------------------------------------------------------------
# Get new message counts
# ------------------------------------------------------------

@router.get("/messages/unseen_messages_counts", summary="Get unseen message counts for current user across all related cases")
async def get_unseen_messages_counts(
    current_user: AppUser = Depends(get_current_user),
    token: str = Depends(get_bearer_or_cookie_token),
):
    """Return flat unseen message counts for the current user across all cases.
    This wraps the standalone unseen_counts_all_cases(encrypted_user_id, session_id) function.
    """
    try:
        from jose import jwt as _jwt
        from app.core.config import settings as _settings
        from app.core.id_codec import set_current_session as _set_sess, reset_current_session as _reset_sess, encode_id as _enc
    except Exception:  # pragma: no cover
        # Fallback local imports (should not happen in normal runtime)
        import jose as _jwt  # type: ignore
        from app.core.config import settings as _settings  # type: ignore
        from app.core.id_codec import set_current_session as _set_sess, reset_current_session as _reset_sess, encode_id as _enc  # type: ignore

    # Decode token to extract session id (jti)
    payload = _jwt.decode(token, _settings.jwt_secret_key, algorithms=[_settings.jwt_algorithm])
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Invalid or missing session id")

    # Encode current user's app_user id under this session context
    ctx = _set_sess(jti)
    try:
        enc_uid = _enc("app_user", int(current_user.id))
    finally:
        try:
            _reset_sess(ctx)
        except Exception:
            pass

    # Delegate to the standalone function
    counts = await unseen_counts_all_cases(enc_uid, jti)
    # counts already uses encrypted ids and is a flat dict[str, int]
    return counts

# ============================================================
# WebSocket Messaging Infrastructure
# ============================================================

import asyncio
import logging
from typing import Dict, Set, Any
from jose import jwt, JWTError
from fastapi import status
from app.core.config import settings
from app.db.session import async_session_maker
from app.services.auth import validate_session


class _WSConnection:
    def __init__(self, websocket: WebSocket, user_id: int, session_id: str):
        self.websocket = websocket
        self.user_id = int(user_id)
        self.session_id = str(session_id)

class _CaseWSManager:
    def __init__(self) -> None:
        # Keyed by raw user_id
        self._subs_by_user: Dict[int, Set[_WSConnection]] = {}
        self._lock = asyncio.Lock()
        #print("WS Manager initialized")

    # SUBSCRIBE -------------------------------------------------
    async def subscribe_user(self, conn: _WSConnection) -> None:
        async with self._lock:
            s = self._subs_by_user.setdefault(int(conn.user_id), set())
            s.add(conn)
            #print("subscribed", {
            #    "event": "subscribe_user",
            #    "user_id": conn.user_id,
            #    "session_id": conn.session_id,
            #    "sub_count": len(s),
            #})

    # DISCONNECT -------------------------------------------------
    async def disconnect(self, conn: _WSConnection) -> None:
        async with self._lock:
            for uid, s in list(self._subs_by_user.items()):
                if conn in s:
                    s.remove(conn)
                    """ print("disconnected", {
                        "event": "disconnect",
                        "user_id": conn.user_id,
                        "session_id": conn.session_id,
                        "sub_count": len(s),
                    })"""
                    if not s:
                        self._subs_by_user.pop(uid, None)

    # PUBLISH Message Count Change ---------------------------
    async def publish_count_change(self, case_id: int):
        await self.publish( "counts.update", case_id)

    # PUBLISH New Reaction ---------------------------
    async def publish_new_reaction(self, case_id: int, message_id: int, reaction: str):
        # Legacy alias: publish a reactions.update event (kept for backward compatibility)
        await self.publish("reactions.update", case_id, message_id=message_id, content=reaction)

    # PUBLISH Message Change ---------------------------
    async def publish_message_change(self, case_id: int, message_id: int):
        await self.publish("messages.change", case_id, message_id=message_id)

    # PUBLISH -------------------------------------------------
    async def publish(self, type: str, case_id: int, message_id: int = None, content: str = None) -> None:

        # print("publish", type, case_id, message_id, content)

        # Determine which users can see this case, then push counts to connected users
        from .case_utils import list_user_ids_for_case
        from app.core.id_codec import set_current_session, reset_current_session, encode_id
        async with async_session_maker() as db:
            user_ids = await list_user_ids_for_case(db, int(case_id))
        async with self._lock:
            # Snapshot of all current connections keyed by user id
            subs_map = {uid: list(conns) for uid, conns in self._subs_by_user.items() if uid in set(user_ids)}
        """print("publishing", {
            "type": type,
            "case_id": int(case_id),
            "message_id": message_id,
            "content": content,
        })"""
        for uid, conns in subs_map.items():
            for conn in conns:
                try:
                    # Build encrypted user id specific to this connection's session
                    ctx = set_current_session(conn.session_id)
                    try:
                        enc_uid = encode_id("app_user", int(uid))
                    finally:
                        try:
                            reset_current_session(ctx)
                        except Exception:
                            pass

                    if type == "counts.update":
                        # Compute counts for this user under their session id
                        counts = await unseen_counts_all_cases(enc_uid, conn.session_id)
                        await conn.websocket.send_json({
                            "type": type,
                            "counts": counts,
                        })
                        # print("delivered_counts", counts)
                    else:
                        # Encode IDs under this connection's session context to ensure correct encryption
                        from app.core.id_codec import set_current_session as _set_sess2, reset_current_session as _reset_sess2, encode_id as _enc2
                        _ctx2 = _set_sess2(conn.session_id)
                        try:
                            enc_case = _enc2("case", int(case_id))
                            enc_mid = _enc2("message", int(message_id)) if message_id is not None else None
                        finally:
                            try:
                                _reset_sess2(_ctx2)
                            except Exception:
                                pass
                        await conn.websocket.send_json({
                            "type": type,
                            "case_id": enc_case,
                            "message_id": enc_mid,
                            "reaction": content,
                        })
                        # print("delivered_reaction", content)
                except Exception:
                    try:
                        await conn.websocket.close()
                    except Exception:
                        pass
                    await self.disconnect(conn)

_ws_manager = _CaseWSManager()

async def _auth_ws_and_get_user(websocket: WebSocket) -> Optional[tuple[AppUser, str]]:
    token: Optional[str] = None
    auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        token = websocket.query_params.get("token")
    if not token:
        token = websocket.cookies.get(getattr(settings, "cookie_name", "access_token"))
    if not token:
        #print("ws_auth_missing_token")
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not email or not jti:
            #print("ws_auth_invalid_payload")
            return None
    except JWTError:
        #print("ws_auth_jwt_error")
        return None

    async with async_session_maker() as db:
        session = await validate_session(db, jti)
        if not session:
            #print("ws_auth_session_not_found", {"jti": jti})
            return None
        user = (await db.execute(select(AppUser).where(AppUser.email == email, AppUser.is_active == True))).scalars().first()
        if not user:
            #print("ws_auth_user_not_found", {"email": email})
            return None
        return (user, jti)

# ------------------------------------------------------------
# Call from client to setup a websocket
# ------------------------------------------------------------
@router.websocket("/messages/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    #print("ws_accept")
    # Expect two query parameters: uid (encrypted app_user.id), sid (session id/jti)
    enc_uid = websocket.query_params.get("uid")
    sid = websocket.query_params.get("sid")
    if not enc_uid or not sid:
        #print("ws_reject", {"reason": "missing_params"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Validate session id and decode user id
    from app.core.id_codec import set_current_session, reset_current_session, decode_id, OpaqueIdError
    ctx_token = set_current_session(sid)
    try:
        async with async_session_maker() as db:
            session = await validate_session(db, sid)
            if not session:
                #print("ws_reject", {"reason": "session_invalid"})
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        try:
            user_id = int(decode_id("app_user", enc_uid))
        except OpaqueIdError:
            #print("ws_reject", {"reason": "uid_decode_failed"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    finally:
        try:
            reset_current_session(ctx_token)
        except Exception:
            pass

    #print("ws_authenticated", {"user_id": user_id})
    conn = _WSConnection(websocket, user_id, sid)
    await _ws_manager.subscribe_user(conn)

    try:
        while True:
            data = await websocket.receive_json()
            action = (data or {}).get("action")
            if action == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                # no-op for unknown/legacy actions
                await websocket.send_json({"type": "ok"})
    except WebSocketDisconnect:


        print("ws_disconnect", {"user_id": conn.user_id})


    finally:
        await _ws_manager.disconnect(conn)
