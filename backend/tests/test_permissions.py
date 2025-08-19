import pytest
from pydantic.v1 import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate
from app.services.user import create_user
from app.services.auth import user_has_permission

from app.db.models.role import Role
from app.db.models.permission import Permission
from app.db.models.role_permission import RolePermission
from app.db.models.app_user_role import AppUserRole


async def _create_user(db: AsyncSession, email: str = "permtest@example.com", password: str = "StrongPassw0rd!"):
    user = await create_user(
        db,
        UserCreate(
            first_name="Perm",
            last_name="Tester",
            email=EmailStr(email),
            password=password,
        ),
    )
    return user


@pytest.mark.asyncio
async def test_user_has_permission(db_session: AsyncSession):
    # Arrange: create a user
    user = await _create_user(db_session, "perm.user@example.com")

    # Create a role and some permissions
    role = Role(name="Editor", code="editor")
    p_read = Permission(name="Read", code="perm.read")
    p_write = Permission(name="Write", code="perm.write")
    p_delete = Permission(name="Delete", code="perm.delete")

    db_session.add_all([role, p_read, p_write, p_delete])
    await db_session.commit()
    # refresh to get IDs
    await db_session.refresh(role)
    await db_session.refresh(p_read)
    await db_session.refresh(p_write)
    await db_session.refresh(p_delete)

    # Link role -> permissions (grant read and write only)
    rp1 = RolePermission(role_id=role.id, permission_id=p_read.id)
    rp2 = RolePermission(role_id=role.id, permission_id=p_write.id)
    db_session.add_all([rp1, rp2])

    # Link user -> role
    ur = AppUserRole(app_user_id=user.id, role_id=role.id)
    db_session.add(ur)

    await db_session.commit()

    # Act & Assert: single permission checks
    assert await user_has_permission(db_session, user.id, "perm.read") is True
    assert await user_has_permission(db_session, user.id, "perm.write") is True
    assert await user_has_permission(db_session, user.id, "perm.delete") is False

    # Multiple permissions: should return subset, deduplicated, preserving order
    requested = [
        "perm.delete",  # not granted
        "perm.read",    # granted
        "perm.read",    # duplicate
        "perm.write",   # granted
        "perm.none",    # not existing
    ]
    result = await user_has_permission(db_session, user.id, requested)
    assert result == ["perm.read", "perm.write"]
