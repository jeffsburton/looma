import asyncio
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from pydantic.v1 import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import UserCreate
from app.services.user import create_user


async def create_test_user(db: AsyncSession, email: str = "test@example.com", password: str = "test_password123"):
    """Helper to create a user directly in the database for testing"""
    user_data = UserCreate(
        first_name="Test",
        last_name="User",
        email=EmailStr(email),
        password=password
    )

    user = await create_user(db, user_data)
    return user, password  # Return both user and plain password for login


@pytest.mark.asyncio
async def test_create_user_and_login(client: AsyncClient, db_session: AsyncSession):
    # Create user directly in DB
    user, password = await create_test_user(db_session, "john@example.com")

    # Login
    login_data = {
        "email": user.email,
        "password": password
    }

    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data

    # Test /me endpoint
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == user.email


@pytest.mark.asyncio
async def test_login_logout_invalidates_token(client: AsyncClient, db_session: AsyncSession):
    # Create user directly in DB
    user, password = await create_test_user(db_session, "jane@example.com")

    # Login
    login_data = {
        "email": user.email,
        "password": password
    }

    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    token_data = response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify token works before logout
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200

    # Logout
    response = await client.post("/api/v1/auth/logout", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"

    # Try to use the same token after logout - should fail
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    login_data = {
        "email": "nonexistent@example.com",
        "password": "wrong_password"
    }

    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_inactive_user_cannot_login(client: AsyncClient, db_session: AsyncSession):
    # Create user directly in DB
    user, password = await create_test_user(db_session, "inactive@example.com")

    # Make user inactive
    user.is_active = False
    db_session.add(user)
    await db_session.commit()

    # Try to login with inactive user
    login_data = {
        "email": user.email,
        "password": password
    }

    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Account is inactive" in response.json()["detail"]



@pytest.mark.asyncio
async def test_expired_token_via_login(client: AsyncClient, db_session: AsyncSession):
    # Create user directly in DB
    user, password = await create_test_user(db_session, "expired@example.com")

    # Patch the settings to use very short expiry (1 second = 1/60 minutes)
    with patch('app.core.config.settings.access_token_expire_minutes', 1/60):
        # Login with patched settings
        login_data = {
            "email": user.email,
            "password": password
        }

        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        token_data = response.json()
        access_token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # Token should work immediately
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200

        # Wait for token to expire
        await asyncio.sleep(2)

        # Token should now be expired
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

