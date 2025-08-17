import re
import pytest
from httpx import AsyncClient
from pydantic.v1 import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.schemas.user import UserCreate
from app.services.user import create_user
from app.db.models.app_user_session import AppUserSession
from app.services.email import get_outbox, clear_outbox


async def create_test_user(db: AsyncSession, email: str = "resetuser@example.com", password: str = "test_password123"):
    user_data = UserCreate(
        first_name="Reset",
        last_name="User",
        email=EmailStr(email),
        password=password
    )
    user = await create_user(db, user_data)
    return user


@pytest.mark.asyncio
async def test_request_password_reset_success(client: AsyncClient, db_session: AsyncSession):
    # Arrange: create user and clear outbox
    user = await create_test_user(db_session, "reset.success@example.com")
    clear_outbox()

    # Act: call endpoint
    resp = await client.post("/api/v1/auth/password-reset/request", json={"email": user.email})

    # Assert: endpoint success
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("message")

    # Assert: email sent
    outbox = get_outbox()
    assert len(outbox) == 1
    msg = outbox[0]
    assert "Password Reset Request" in msg["Subject"]
    assert user.email in (msg.get("To") or "")

    # Extract token from email body (expects absolute URL .../reset-password?token=<token>)
    # Obtain the plain text body even if the email is multipart
    if msg.is_multipart():
        text_part = msg.get_body(preferencelist=('plain',))
        assert text_part is not None, "Plain text part missing in multipart email"
        text = text_part.get_content()
    else:
        text = msg.get_content()
    m = re.search(r"https?://[^\s]+/reset-password\?token=([0-9a-fA-F]{32})", text)
    assert m, f"Reset link with token not found in email body: {text}"
    token = m.group(1)

    # Verify token stored in DB for the user and active
    stmt = select(AppUserSession).where(AppUserSession.jti == token)
    result = await db_session.execute(stmt)
    session = result.scalars().first()
    assert session is not None
    assert session.app_user_id == user.id
    assert session.is_active is True


@pytest.mark.asyncio
async def test_request_password_reset_nonexistent_email(client: AsyncClient):
    clear_outbox()
    resp = await client.post("/api/v1/auth/password-reset/request", json={"email": "doesnotexist@example.com"})
    assert resp.status_code == 404
    assert resp.json()["detail"] in ("Email not found", "User not found")
    # Ensure no email was sent
    outbox = get_outbox()
    assert len(outbox) == 0
