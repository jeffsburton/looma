from pydantic import BaseModel, EmailStr, ConfigDict

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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )

class UserInfo(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 123,
                "email": "user@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "is_active": True
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
