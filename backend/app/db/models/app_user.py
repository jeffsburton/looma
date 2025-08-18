from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db import Base, TimestampMixin

class AppUser(Base, TimestampMixin):
    __tablename__ = "app_user"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    phone = Column(String(20), nullable=True)
    organization = Column(String(200), nullable=True)
    referred_by = Column(String(100), nullable=True)

    sessions = relationship(
        "AppUserSession",
        back_populates="app_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )