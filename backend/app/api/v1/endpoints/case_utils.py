from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.id_codec import decode_id, OpaqueIdError
from app.db.models.app_user_case import AppUserCase
from app.db.models.person import Person
from app.db.models.person_team import PersonTeam
from app.db.models.team_case import TeamCase


def _decode_or_404(model: str, opaque_id: str) -> int:
    """
    Decode an opaque id for a given model. Plain numeric ids are NOT accepted.
    Raises 404 HTTPException if the id is invalid or session context is missing.
    """
    try:
        return decode_id(model, opaque_id)
    except OpaqueIdError:
        raise HTTPException(status_code=404, detail=f"{model.replace('_', ' ').title()} not found")


async def can_user_access_case(db: AsyncSession, user_id: int, case_id: int) -> bool:
    """
    Returns True if the user can access the given case based on:
      - Global permission CASES.ALL_CASES
      - Direct assignment via app_user_case
      - Team membership via person -> person_team -> team_case
    """
    # 1) Global permission check (users with CASES.ALL_CASES can access any case)
    from app.db.models.app_user_role import AppUserRole
    from app.db.models.role_permission import RolePermission
    from app.db.models.permission import Permission

    has_all_cases = (
        await db.execute(
            select(1)
            .select_from(AppUserRole)
            .join(RolePermission, RolePermission.role_id == AppUserRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(and_(AppUserRole.app_user_id == user_id, Permission.code == "CASES.ALL_CASES"))
            .limit(1)
        )
    ).first() is not None

    if has_all_cases:
        return True

    # 2) Direct assignment
    direct_exists = (
        await db.execute(
            select(1).where(and_(AppUserCase.app_user_id == user_id, AppUserCase.case_id == case_id)).limit(1)
        )
    ).first() is not None

    if direct_exists:
        return True

    # 3) Team-based access
    team_exists_stmt = (
        select(1)
        .select_from(Person)
        .join(PersonTeam, PersonTeam.person_id == Person.id)
        .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
        .where(and_(Person.app_user_id == user_id, TeamCase.case_id == case_id))
        .limit(1)
    )
    team_exists = (await db.execute(team_exists_stmt)).first() is not None
    return team_exists


async def list_user_ids_for_case(db: AsyncSession, case_id: int) -> list[int]:
    """
    Return distinct AppUser IDs who can access the case via:
      - Global permission CASES.ALL_CASES
      - Direct assignment in app_user_case
      - Team membership (person -> person_team -> team_case)
    """
    # Directly assigned users
    from app.db.models.app_user_case import AppUserCase
    direct_rows = (
        await db.execute(
            select(AppUserCase.app_user_id).where(AppUserCase.case_id == case_id)
        )
    ).scalars().all() or []

    # Users via teams linked to the case
    team_user_rows = (
        await db.execute(
            select(Person.app_user_id)
            .select_from(Person)
            .join(PersonTeam, PersonTeam.person_id == Person.id)
            .join(TeamCase, TeamCase.team_id == PersonTeam.team_id)
            .where(TeamCase.case_id == case_id)
        )
    ).scalars().all() or []

    # Users with global permission CASES.ALL_CASES
    from app.db.models.app_user_role import AppUserRole
    from app.db.models.role_permission import RolePermission
    from app.db.models.permission import Permission
    all_cases_user_rows = (
        await db.execute(
            select(AppUserRole.app_user_id)
            .select_from(AppUserRole)
            .join(RolePermission, RolePermission.role_id == AppUserRole.role_id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(Permission.code == "CASES.ALL_CASES")
        )
    ).scalars().all() or []

    # Distinct, filter out nulls
    ids: set[int] = set(int(x) for x in direct_rows if x is not None)
    ids.update(int(x) for x in team_user_rows if x is not None)
    ids.update(int(x) for x in all_cases_user_rows if x is not None)
    return sorted(ids)
