from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class AppUserSession(Base):
    __tablename__ = "app_user_session"

    id = Column(Integer, primary_key=True, index=True)
    app_user_id = Column(Integer, ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    jti = Column(String(255), unique=True, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    app_user = relationship("AppUser", back_populates="sessions")