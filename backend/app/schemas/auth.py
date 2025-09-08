from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.mixins import OpaqueIdMixin

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "YourSecurePassword123"
            }
        }
    )

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    codes: list[str] = []

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "codes": ["users.read", "users.write"]
            }
        }
    )

class UserInfo(OpaqueIdMixin):
    OPAQUE_MODEL = "app_user"
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    session_id: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "1.gAAAAABl...",  # opaque id example
                "email": "user@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "is_active": True,
                "session_id": "b1d2c3e4-...-jti"
            }
        }
    )


class PasswordResetRequest(BaseModel):
    email: EmailStr

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "3f2a1b4c5d6e7f8091a2b3c4d5e6f708",
                "new_password": "NewSecurePassword123"
            }
        }
    )


class MessageResponse(BaseModel):
    message: str
