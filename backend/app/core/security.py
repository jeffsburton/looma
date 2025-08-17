from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Use pbkdf2_sha256 to avoid runtime issues with bcrypt backend versions
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def create_access_token(*, sub: str, jti: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token"""
    to_encode: Dict[str, Any] = {"sub": sub, "jti": jti}

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode["exp"] = int(expire.timestamp())
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)