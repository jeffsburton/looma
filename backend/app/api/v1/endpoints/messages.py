from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Body, WebSocket, WebSocketDisconnect
from sqlalchemy import select
import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

from app.api.dependencies import get_current_user
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

from .case_utils import _decode_or_404, can_user_access_case
from app.schemas.message import MessageRead

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


@router.get("/{case_id}/messages", summary="List messages for a case", response_model=List[MessageRead])
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
                created_at=r.created_at,
                updated_at=r.updated_at,
                writer_name=getattr(r, "writer_name", None),
                seen=bool(getattr(r, "seen", False)),
                reaction=getattr(r, "reaction", None),
                reply_to_text=getattr(r, "reply_to_text", None),
                is_mine=bool(is_mine),
                writer_photo_url=writer_photo_url,
                my_photo_url=my_photo_url,
            )
        )
    return items


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

    msg = Message(case_id=pk, written_by_id=int(pid), message=payload.message, reply_to_id=rid)
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
    msg_model = MessageRead(
        id=int(msg.id),
        case_id=int(msg.case_id),
        written_by_id=int(msg.written_by_id) if msg.written_by_id is not None else None,
        message=msg.message,
        reply_to_id=int(msg.reply_to_id) if msg.reply_to_id is not None else None,
        created_at=msg.created_at,
        updated_at=msg.updated_at,
        writer_name=writer_name,
        reaction=None,
        reply_to_text=reply_to_text,
        is_mine=True,  # author sees their own pushed message as mine
        writer_photo_url=writer_photo_url,
        my_photo_url=None,  # filled per-connection in ws manager
    )

    # Publish to subscribers of this case (per-connection fields will be added by manager)
    try:
        ws_payload = msg_model.model_dump(mode="json")
        ws_payload["author_person_id"] = int(pid)
        await _ws_manager.publish(int(msg.case_id), ws_payload)
    except Exception:
        # Do not fail the request if broadcasting fails
        pass

    # Return encrypted payload
    return msg_model



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


@router.get("/messages/unseen_counts", summary="Get unseen message counts for current user across all related cases")
async def unseen_counts_all_cases(
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    # Resolve current user's person id
    pid = (await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))).scalar_one_or_none()
    if pid is None:
        raise HTTPException(status_code=400, detail="Current user is not linked to a person")

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

    rows = (await db.execute(q)).all()

    # Aggregate into the requested JSON shape
    by_case: dict[int, dict] = {}
    for r in rows:
        cid = int(r.case_id)
        cnt = int(getattr(r, "cnt", 0) or 0)
        if cnt <= 0:
            continue
        entry = by_case.setdefault(
            cid,
            {
                "case_id": encode_id("case", cid),
                "count": 0,
                "rfis": [],
                "ops_plans": [],
                "tasks": [],
            },
        )
        # Add to total
        entry["count"] += cnt

        # Breakdown arrays, respecting mutual exclusivity
        rid = r.rfi_id
        oid = r.ops_plan_id
        tid = r.task_id
        if rid is not None:
            entry["rfis"].append({"rfi_id": encode_id("rfi", int(rid)), "count": cnt})
        elif oid is not None:
            entry["ops_plans"].append({"ops_plan_id": int(oid), "count": cnt})
        elif tid is not None:
            # Note: spec uses key 'tasks_id' inside tasks array
            entry["tasks"].append({"tasks_id": int(tid), "count": cnt})
        else:
            # Plain case-level messages without rfi/ops_plan/task: only included in total
            pass

    # Return as a list; omit cases with zero total (none collected)
    # Optionally sort by total desc, then by case id
    result = sorted(by_case.values(), key=lambda x: (-int(x["count"]), str(x["case_id"])))
    return result

# --- WebSocket Messaging Infrastructure ---
import asyncio
import logging
from typing import Dict, Set, Any
from jose import jwt, JWTError
from fastapi import status
from app.core.config import settings
from app.db.session import async_session_maker
from app.services.auth import validate_session


class _WSConnection:
    def __init__(self, websocket: WebSocket, user_id: int, person_id: int, my_photo_url: str):
        self.websocket = websocket
        self.user_id = int(user_id)
        self.person_id = int(person_id)
        self.my_photo_url = my_photo_url

class _CaseWSManager:
    def __init__(self) -> None:
        self._channels: Dict[int, Set[_WSConnection]] = {}
        self._lock = asyncio.Lock()
        print("WS Manager initialized")

    async def subscribe(self, case_id: int, conn: _WSConnection) -> None:
        async with self._lock:
            s = self._channels.setdefault(int(case_id), set())
            s.add(conn)
            print("subscribed", {
                "event": "subscribe",
                "case_id": int(case_id),
                "user_id": conn.user_id,
                "person_id": conn.person_id,
                "sub_count": len(s),
            })

    async def unsubscribe(self, case_id: int, conn: _WSConnection) -> None:
        async with self._lock:
            s = self._channels.get(int(case_id))
            if s and conn in s:
                s.remove(conn)
                print("unsubscribed", {
                    "event": "unsubscribe",
                    "case_id": int(case_id),
                    "user_id": conn.user_id,
                    "person_id": conn.person_id,
                    "sub_count": len(s),
                })
                if not s:
                    self._channels.pop(int(case_id), None)

    async def disconnect(self, conn: _WSConnection) -> None:
        async with self._lock:
            for cid, s in list(self._channels.items()):
                if conn in s:
                    s.remove(conn)
                    print("disconnected", {
                        "event": "disconnect",
                        "case_id": int(cid),
                        "user_id": conn.user_id,
                        "person_id": conn.person_id,
                        "sub_count": len(s),
                    })
                    if not s:
                        self._channels.pop(cid, None)

    async def publish(self, case_id: int, base_payload: Dict[str, Any]) -> None:
        # Broadcast to all subscribers of this case
        async with self._lock:
            subs = list(self._channels.get(int(case_id), set()))
        print("publish", {
            "event": "publish",
            "case_id": int(case_id),
            "message_id": base_payload.get("id"),
            "written_by_id": base_payload.get("written_by_id"),
            "subscriber_count": len(subs),
        })
        for conn in subs:
            try:
                # Prefer an internal raw author_person_id if provided
                raw_author_id = base_payload.get("author_person_id")
                is_mine = (int(raw_author_id) == conn.person_id) if raw_author_id is not None else False
                payload = dict(base_payload)
                # Remove internal field before sending to client
                if "author_person_id" in payload:
                    payload.pop("author_person_id", None)
                payload["is_mine"] = bool(is_mine)
                payload["my_photo_url"] = conn.my_photo_url
                # For pushed items, mark seen True for the author, False for others
                payload["seen"] = bool(is_mine)
                await conn.websocket.send_json({
                    "type": "message.created",
                    "case_id": int(case_id),
                    "message": payload,
                })
                print("delivered", {
                    "event": "deliver",
                    "case_id": int(case_id),
                    "message_id": base_payload.get("id"),
                    "to_person_id": conn.person_id,
                    "to_user_id": conn.user_id,
                    "is_mine": bool(is_mine),
                })
            except Exception as e:
                print("deliver_failed")
                # best-effort; drop failures silently
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
        print("ws_auth_missing_token")
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        jti: str = payload.get("jti")
        if not email or not jti:
            print("ws_auth_invalid_payload")
            return None
    except JWTError:
        print("ws_auth_jwt_error")
        return None

    async with async_session_maker() as db:
        session = await validate_session(db, jti)
        if not session:
            print("ws_auth_session_not_found", {"jti": jti})
            return None
        user = (await db.execute(select(AppUser).where(AppUser.email == email, AppUser.is_active == True))).scalars().first()
        if not user:
            print("ws_auth_user_not_found", {"email": email})
            return None
        return (user, jti)

@router.websocket("/messages/ws")
async def websocket_messages(websocket: WebSocket):
    await websocket.accept()
    print("ws_accept")
    auth = await _auth_ws_and_get_user(websocket)
    if not auth:
        print("ws_reject", {"reason": "auth_failed"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    user, jti = auth

    # Establish id_codec session context for the duration of this WS
    from app.core.id_codec import set_current_session, reset_current_session
    ctx_token = set_current_session(jti)

    # Resolve person and compute my photo url once
    async with async_session_maker() as db:
        pid = (await db.execute(select(Person.id).where(Person.app_user_id == user.id))).scalar_one_or_none()
        if pid is None:
            print("ws_reject", {"reason": "no_person", "user_id": user.id})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            reset_current_session(ctx_token)
            return
        me_has_pic = (await db.execute(select(Person.profile_pic.isnot(None)).where(Person.id == pid))).scalar() or False
        my_photo_url = f"/api/v1/media/pfp/person/{encode_id('person', int(pid))}?s=xs" if me_has_pic else "/images/pfp-generic.png"

    print("ws_authenticated", {"user_id": user.id, "person_id": int(pid)})
    conn = _WSConnection(websocket, user.id, int(pid), my_photo_url)

    try:
        while True:
            data = await websocket.receive_json()
            action = (data or {}).get("action")
            if action == "subscribe":
                ids = data.get("case_ids") or []
                accepted: list[int] = []
                denied: list[Any] = []
                async with async_session_maker() as db:
                    for cid in ids:
                        # decode opaque id strictly (no numeric fallback)
                        try:
                            pk = decode_id("case", cid)
                        except Exception:
                            denied.append(cid)
                            continue
                        if await can_user_access_case(db, user.id, int(pk)):
                            await _ws_manager.subscribe(int(pk), conn)
                            accepted.append(int(pk))
                        else:
                            denied.append(cid)
                print("ws_subscribe", {
                    "user_id": conn.user_id,
                    "person_id": conn.person_id,
                    "accepted": accepted,
                    "denied": denied,
                })
                await websocket.send_json({"type": "subscribed", "accepted": accepted, "denied": denied})
            elif action == "unsubscribe":
                ids = data.get("case_ids") or []
                for cid in ids:
                    try:
                        pk = decode_id("case", cid)
                    except Exception:
                        continue
                    await _ws_manager.unsubscribe(int(pk), conn)
                print("ws_unsubscribe", {
                    "user_id": conn.user_id,
                    "person_id": conn.person_id,
                    "case_ids": ids,
                })
                await websocket.send_json({"type": "unsubscribed", "case_ids": ids})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                print("ws_unknown_action", {"action": action})
                await websocket.send_json({"type": "error", "error": "Unknown action"})
    except WebSocketDisconnect:
        print("ws_disconnect", {"user_id": conn.user_id, "person_id": conn.person_id})
    finally:
        await _ws_manager.disconnect(conn)
        try:
            reset_current_session(ctx_token)
        except Exception:
            pass
