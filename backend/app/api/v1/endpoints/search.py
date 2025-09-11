from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, asc
from sqlalchemy.ext.asyncio import AsyncSession
import sqlalchemy as sa

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.case import Case
from app.db.models.subject import Subject
from app.db.models.task import Task
from app.db.models.message import Message
from app.db.models.app_user_case import AppUserCase
from app.db.models.person import Person
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase
from app.schemas.search import SearchResponse, SearchHit
from app.core.id_codec import encode_id
from app.services.global_search_registry import REGISTRY

router = APIRouter()


# --- Core: registry-driven union (no joins) -> (table_name, column_name, record_id) ---
_MODEL_MAP: Dict[str, Any] = {
    "case": Case,
    "task": Task,
    "message": Message,
}


def _build_core_union(q_like: str, wanted: set[str] | set) -> sa.sql.Selectable:
    """
    Build a UNION ALL of simple selects per registry entry that each return:
      table_name (literal), column_name (literal), record_id (pk)
    No joins. Columns come from global_search_registry.REGISTRY.
    """
    parts: List[sa.sql.Select] = []
    for entry in REGISTRY:
        table = entry.get("table")
        if not table or (wanted and table not in wanted):
            continue
        model = _MODEL_MAP.get(table)
        if model is None:
            continue
        cols = entry.get("columns") or []
        for col in cols:
            # Ensure the column exists on the model; skip if not
            try:
                column_obj = getattr(model, col)
            except Exception:
                continue
            parts.append(
                select(
                    sa.literal(table).label("table_name"),
                    sa.literal(col).label("column_name"),
                    model.id.label("record_id"),
                ).where(column_obj.ilike(q_like))
            )
    if not parts:
        # empty selectable that returns no rows but has the right shape
        return select(
            sa.literal("").label("table_name"),
            sa.literal("").label("column_name"),
            sa.literal(-1).label("record_id"),
        ).where(sa.text("1=0"))
    core = parts[0]
    for p in parts[1:]:
        core = core.union_all(p)
    return core


def _access_filter_case(db_user_id: int):
    """Return SQLAlchemy OR filter granting access to cases for the current user."""
    # direct assignment
    direct = (AppUserCase.app_user_id == db_user_id) & (AppUserCase.case_id == Case.id)
    # team membership path person -> person_team -> team_case
    from sqlalchemy import exists, and_  # local import to avoid top-level clutter
    team_exists = exists(
        select(1)
        .select_from(Person)
        .join(PersonTeam, PersonTeam.person_id == Person.id)
        .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
        .where(and_(Person.app_user_id == db_user_id, TeamCase.case_id == Case.id))
    )
    return or_(exists(select(1).where(direct)), team_exists)


def _score_text(value: Optional[str], q: str, base: float) -> float:
    if not value:
        return 0.0
    v = value.lower()
    t = q.lower()
    if not t:
        return 0.0
    score = base
    if v.startswith(t):
        score += 0.5
    elif t in v:
        score += 0.25
    return score


@router.get("/search", response_model=SearchResponse, summary="Global search across cases, tasks, and messages")
async def global_search(
    q: str = Query(..., min_length=1),
    types: Optional[str] = Query(None, description="CSV of entity tables to search (case,task,message)"),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    q_like = f"%{q}%"
    wanted = {t.strip() for t in (types.split(',') if types else []) if t.strip()}

    # Phase 1: core union (no joins) -> collect matched ids per table
    core_union = _build_core_union(q_like, wanted)
    core_rows = (await db.execute(core_union)).all()

    ids_by_table: Dict[str, List[int]] = {}
    for table_name, _column_name, record_id in core_rows:
        if record_id is None:
            continue
        t = str(table_name)
        ids_by_table.setdefault(t, [])
        rid = int(record_id)
        # dedupe
        if rid not in ids_by_table[t]:
            ids_by_table[t].append(rid)

    hits: List[SearchHit] = []

    # Phase 2: enrich per table with joins/access control as needed
    from app.services.auth import user_has_permission

    # CASE enrichment
    if (not wanted or 'case' in wanted) and ids_by_table.get('case'):
        case_ids = ids_by_table['case'][:100]
        stmt = (
            select(
                Case.id.label('case_id'),
                Case.case_number,
                Subject.first_name,
                Subject.last_name,
                Subject.profile_pic.isnot(None).label('has_pic'),
            )
            .join(Subject, Subject.id == Case.subject_id)
            .where(Case.id.in_(case_ids))
            .order_by(asc(Subject.last_name), asc(Subject.first_name))
        )
        if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
            from sqlalchemy import and_, exists
            direct_exists = exists(select(1).where(and_(AppUserCase.app_user_id == current_user.id, AppUserCase.case_id == Case.id)))
            team_exists = exists(
                select(1)
                .select_from(Person)
                .join(PersonTeam, PersonTeam.person_id == Person.id)
                .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
                .where(and_(Person.app_user_id == current_user.id, TeamCase.case_id == Case.id))
            )
            stmt = stmt.where(or_(direct_exists, team_exists))
        rows = (await db.execute(stmt)).all()
        base = next((e.get('boost', 1.0) for e in REGISTRY if e["table"] == "case"), 1.0)
        for case_id, case_number, first, last, has_pic in rows:
            title = f"{first} {last}".strip() or "Case"
            subtitle = f"Case {case_number}"
            hits.append(SearchHit(
                title=title,
                subtitle=subtitle,
                icon=None,
                thumbnail_url=None,
                entity_type='case',
                entity_id=encode_id('case', int(case_id)),
                parent_case_id=None,
                parent_case_number=case_number,
                primary_path=f"/cases/{case_number}/core/intake",
                alt_paths=[],
                score=base,
            ))

    # TASK enrichment
    if (not wanted or 'task' in wanted) and ids_by_table.get('task'):
        task_ids = ids_by_table['task'][:100]
        stmt = (
            select(
                Task.id.label('task_id'),
                Task.title,
                Case.id.label('case_id'),
                Case.case_number,
            )
            .join(Case, Case.id == Task.case_id)
            .where(Task.id.in_(task_ids))
        )
        if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
            from sqlalchemy import and_, exists
            direct_exists = exists(select(1).where(and_(AppUserCase.app_user_id == current_user.id, AppUserCase.case_id == Case.id)))
            team_exists = exists(
                select(1)
                .select_from(Person)
                .join(PersonTeam, PersonTeam.person_id == Person.id)
                .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
                .where(and_(Person.app_user_id == current_user.id, TeamCase.case_id == Case.id))
            )
            stmt = stmt.where(or_(direct_exists, team_exists))
        rows = (await db.execute(stmt)).all()
        base = next((e.get('boost', 1.0) for e in REGISTRY if e["table"] == "task"), 1.0)
        for task_id, title, case_id, case_number in rows:
            title_safe = title or "Untitled task"
            score = _score_text(title_safe, q, base)
            hits.append(SearchHit(
                title=title_safe,
                subtitle=f"Case {case_number}",
                icon="assignment",
                thumbnail_url=None,
                entity_type='task',
                entity_id=encode_id('task', int(task_id)),
                parent_case_id=encode_id('case', int(case_id)),
                parent_case_number=case_number,
                primary_path=f"/cases/{case_number}/tasks/{int(task_id)}",
                alt_paths=[f"/cases/{case_number}/tasks"],
                score=score,
            ))

    # MESSAGE enrichment
    if (not wanted or 'message' in wanted) and ids_by_table.get('message'):
        message_ids = ids_by_table['message'][:100]
        stmt = (
            select(
                Message.id.label('message_id'),
                Message.message,
                Message.task_id,
                Case.id.label('case_id'),
                Case.case_number,
            )
            .join(Case, Case.id == Message.case_id)
            .where(Message.id.in_(message_ids))
        )
        if not await user_has_permission(db, current_user.id, "CASES.ALL_CASES"):
            from sqlalchemy import and_, exists
            direct_exists = exists(select(1).where(and_(AppUserCase.app_user_id == current_user.id, AppUserCase.case_id == Case.id)))
            team_exists = exists(
                select(1)
                .select_from(Person)
                .join(PersonTeam, PersonTeam.person_id == Person.id)
                .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
                .where(and_(Person.app_user_id == current_user.id, TeamCase.case_id == Case.id))
            )
            stmt = stmt.where(or_(direct_exists, team_exists))
        rows = (await db.execute(stmt)).all()
        base = next((e.get('boost', 1.0) for e in REGISTRY if e["table"] == "message"), 1.0)
        for message_id, text, task_id, case_id, case_number in rows:
            title = (text or "").strip()
            if len(title) > 120:
                title = title[:117] + "..."
            score = _score_text(text or "", q, base)
            if task_id is not None:
                primary = f"/cases/{case_number}/tasks/{int(task_id)}"
                alts = [f"/cases/{case_number}/messages"]
            else:
                primary = f"/cases/{case_number}/messages"
                alts = []
            hits.append(SearchHit(
                title=title or "Message",
                subtitle=f"Case {case_number}",
                icon="chat_bubble",
                thumbnail_url=None,
                entity_type='message',
                entity_id=encode_id('message', int(message_id)),
                parent_case_id=encode_id('case', int(case_id)),
                parent_case_number=case_number,
                primary_path=primary,
                alt_paths=alts,
                score=score,
            ))

    # Merge-sort-limit
    hits.sort(key=lambda h: -(h.score or 0))
    if len(hits) > limit:
        hits = hits[:limit]

    return SearchResponse(query=q, hits=hits)
