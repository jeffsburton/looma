import os
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Load from .env if present; still honor real environment variables first
    model_config = SettingsConfigDict(env_file=".env")

    # Database
    # Read DATABASE_URL directly from environment when constructing settings,
    # falling back to the default sqlite URL.
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db"))

    # JWT
    jwt_secret_key: str = "your-super-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Password reset
    password_reset_token_expire_minutes: int = 60

    # Frontend URL configuration (for links in emails)
    # Select environment: development | training | production
    frontend_env: str = "development"
    # Base URLs for each environment (can be overridden via env)
    frontend_base_url: str = "http://localhost:5173"
    training_frontend_base_url: str = "https://looma-training.c2r.one"
    production_frontend_base_url: str = "https://looma.c2r.one"

    # Cookies
    cookie_name: str = "access_token"
    cookie_secure: bool = False  # set True in production over HTTPS
    cookie_samesite: str = "lax"  # "lax" or "strict" or "none" (with secure True)
    cookie_domain: Optional[str] = None  # e.g., ".example.com" in prod; None in dev
    cookie_path: str = "/"

    # CSRF (Double-Submit Cookie) - disabled by default for backward compatibility
    csrf_protection_enabled: bool = False
    csrf_cookie_name: str = "csrf_token"
    csrf_header_name: str = "X-CSRF-Token"

    # Session Management
    session_inactivity_timeout_minutes: int = 60

    # App
    project_name: str = "Looma Case Management System"
    debug: bool = False

    # Admin notifications
    admin_notification_email: Optional[str] = "jsburton@gmail.com"

    # Email (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = "looma.c2r@gmail.com"
    smtp_password: Optional[str] = "rfxxprpasmeuqiin"
    smtp_use_tls: bool = True  # STARTTLS on port 587
    smtp_from: Optional[str] = None  # default to smtp_username if None
    email_backend: str = "smtp"  # options: smtp | console | memory

    @property
    def effective_frontend_base_url(self) -> str:
        env = (self.frontend_env or "development").lower().strip()
        if env == "production":
            return self.production_frontend_base_url
        if env == "training":
            return self.training_frontend_base_url
        # default to development
        return self.frontend_base_url

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        # Normalize to psycopg3 driver for application runtime while leaving Alembic to use DATABASE_URL directly.
        # Handle common Postgres URL variants and coerce to psycopg.
        if v.startswith("postgres://"):
            # Old-style URLs sometimes used by cloud providers
            v = v.replace("postgres://", "postgresql://", 1)
        if v.startswith("postgresql+psycopg2://"):
            v = v.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        # If asyncpg was specified, prefer psycopg for Python 3.13 compatibility on Render
        elif v.startswith("postgresql+asyncpg://"):
            v = v.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        # leave sqlite+aiosqlite and already-async URLs unchanged
        return v


settings = Settings()