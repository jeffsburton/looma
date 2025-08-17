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
async def test_register_success(client: AsyncClient):
    """Test successful user registration"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "securepassword123"
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert data["email"] == "john.doe@example.com"
    assert data["is_active"] is True
    assert "password" not in data  # Password should not be in response
    assert "password_hash" not in data  # Password hash should not be in response
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_register_with_optional_fields(client: AsyncClient):
    """Test user registration with optional fields"""
    user_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "password": "securepassword123",
        "phone": "+1234567890",
        "organization": "Test Company",
        "referred_by": "John Doe"
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] == "+1234567890"
    assert data["organization"] == "Test Company"
    assert data["referred_by"] == "John Doe"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session):
    """Test registration with duplicate email"""
    # First, create a user
    await create_test_user(db_session, "duplicate@example.com")

    # Try to register with the same email
    user_data = {
        "first_name": "Another",
        "last_name": "User",
        "email": "duplicate@example.com",
        "password": "anotherpassword123"
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient):
    """Test registration with invalid email"""
    user_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "invalid-email",
        "password": "password123"
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_missing_required_fields(client: AsyncClient):
    """Test registration with missing required fields"""
    user_data = {
        "first_name": "Test",
        "email": "test@example.com"
        # Missing last_name and password
    }

    response = await client.post("/api/v1/auth/register", json=user_data)

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_then_login(client: AsyncClient):
    """Test that a registered user can successfully login"""
    # Register a user
    user_data = {
        "first_name": "Login",
        "last_name": "Test",
        "email": "logintest@example.com",
        "password": "testpassword123"
    }

    register_response = await client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 201

    # Now try to login
    login_data = {
        "email": "logintest@example.com",
        "password": "testpassword123"
    }

    login_response = await client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()