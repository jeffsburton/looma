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
      - Direct assignment via app_user_case
      - Team membership via person -> person_team -> team_case
    """
    direct_exists = (
        await db.execute(
            select(1).where(and_(AppUserCase.app_user_id == user_id, AppUserCase.case_id == case_id)).limit(1)
        )
    ).first() is not None

    if direct_exists:
        return True

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
