from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.db.models.app_user import AppUser
from app.services.auth import user_has_permission

# Protect all endpoints in this router with authentication
router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("/has_perms", response_model=List[str], summary="Filter permissions the current user has")
async def has_perms(
    permission_codes: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
) -> List[str]:
    """
    Given a list of permission codes (strings), return the subset that the
    current authenticated user actually has.

    This uses a single SQL query (Permission.code IN (...)) under the hood to
    minimize round-trips when multiple permissions are provided.
    """
    if not permission_codes:
        return []

    # Delegate to the vectorized form of user_has_permission to do one query
    found = await user_has_permission(db, current_user.id, permission_codes)
    # Type narrowing: function returns List[str] for list input
    return list(found)
