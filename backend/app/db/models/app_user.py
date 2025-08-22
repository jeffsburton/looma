from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.db import Base, TimestampMixin

class AppUser(Base, TimestampMixin):
    __tablename__ = "app_user"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default="true")

    telegram = Column(String(50), nullable=True)
    onboarding_data = Column(Text, nullable=True)

    sessions = relationship(
        "AppUserSession",
        back_populates="app_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )