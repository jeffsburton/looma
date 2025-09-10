from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy import select, or_, and_, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_permission
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.db.models.person import Person
from app.db.models.task import Task
from app.core.id_codec import decode_id, OpaqueIdError, encode_id

from .case_utils import _decode_or_404, can_user_access_case
from app.schemas.task import TaskRead, TaskCreate, TaskPartial

router = APIRouter()


@router.get("/{case_id}/tasks", summary="List tasks for a case", response_model=List[TaskRead])
async def list_tasks(
    case_id: str,
    q: Optional[str] = None,
    completed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    conditions = [Task.case_id == int(case_db_id)]

    # Filter completed state if provided; default is show non-completed when completed == False
    if completed is True:
        conditions.append(Task.completed.is_(True))
    elif completed is False:
        conditions.append(Task.completed.is_(False))

    if q:
        s = f"%{q.strip()}%"
        conditions.append(or_(Task.title.ilike(s), Task.description.ilike(s)))

    rows = (
        await db.execute(
            select(Task)
            .where(and_(*conditions))
            .order_by(asc(Task.completed), asc(Task.ready_for_review), asc(Task.id))
        )
    ).scalars().all()

    return [TaskRead.model_validate(r) for r in rows]


@router.post(
    "/{case_id}/tasks",
    summary="Create a new task for a case",
    dependencies=[Depends(require_permission("TASKS.CREATE"))],
    response_model=TaskRead,
)
async def create_task(
    case_id: str,
    payload: TaskCreate = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    # Resolve assigned_by_id: explicit opaque person id or default to current user's person
    assigned_by_db_id: Optional[int] = None
    if payload.assigned_by_id:
        try:
            assigned_by_db_id = int(decode_id("person", payload.assigned_by_id))
        except OpaqueIdError:
            raise HTTPException(status_code=400, detail="Invalid assigned_by_id")
    else:
        assigned_by_db_id = (
            await db.execute(select(Person.id).where(Person.app_user_id == current_user.id))
        ).scalar_one_or_none()
        if assigned_by_db_id is None:
            raise HTTPException(status_code=400, detail="Current user is not linked to a person")

    row = Task(
        case_id=int(case_db_id),
        assigned_by_id=int(assigned_by_db_id),
        title=title,
        description=(payload.description or ""),
        response=None,
        ready_for_review=False,
        completed=False,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return TaskRead.model_validate(row)


@router.get("/{case_id}/tasks/{task_id}", summary="Get a task for a case", response_model=TaskRead)
async def get_task(
    case_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        task_db_id = int(decode_id("task", task_id)) if not str(task_id).isdigit() else int(task_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Task not found")

    row = (
        await db.execute(select(Task).where(Task.id == int(task_db_id), Task.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskRead.model_validate(row)


@router.patch("/{case_id}/tasks/{task_id}", summary="Update a task for a case", response_model=TaskRead)
async def update_task(
    case_id: str,
    task_id: str,
    payload: TaskPartial = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    case_db_id = _decode_or_404("case", case_id)
    if not await can_user_access_case(db, current_user.id, int(case_db_id)):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        task_db_id = int(decode_id("task", task_id)) if not str(task_id).isdigit() else int(task_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail="Task not found")

    row = (
        await db.execute(select(Task).where(Task.id == int(task_db_id), Task.case_id == int(case_db_id)))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    # Determine which fields are being changed
    fields_set = getattr(payload, "model_fields_set", set())

    # Enforce permissions per field
    changing_completed = ("completed" in fields_set)
    if changing_completed:
        # Need TASKS.COMPLETE to toggle completion
        await require_permission("TASKS.COMPLETE")(db=db, current_user=current_user)  # type: ignore

    changing_other = bool(fields_set - {"completed"})
    if changing_other:
        # Need TASKS.CREATE for other edits per UI constraints
        await require_permission("TASKS.CREATE")(db=db, current_user=current_user)  # type: ignore

    # Apply updates
    if "title" in fields_set:
        row.title = (payload.title or "").strip()
    if "description" in fields_set:
        row.description = payload.description or ""
    if "response" in fields_set:
        row.response = (payload.response or None)
    if "ready_for_review" in fields_set:
        row.ready_for_review = bool(payload.ready_for_review) if payload.ready_for_review is not None else False
    if "completed" in fields_set:
        row.completed = bool(payload.completed) if payload.completed is not None else False
    if "assigned_by_id" in fields_set:
        new_val = None
        if payload.assigned_by_id is not None:
            s = str(payload.assigned_by_id)
            if s == "":
                new_val = None
            else:
                try:
                    new_val = int(decode_id("person", s)) if not s.isdigit() else int(s)
                except Exception:
                    new_val = None
        row.assigned_by_id = new_val or row.assigned_by_id

    await db.commit()
    await db.refresh(row)

    return TaskRead.model_validate(row)
