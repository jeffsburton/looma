from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import ForeignKey

from app.db import Base


class Team(Base):
    __tablename__ = "team"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    inactive = Column(Boolean, nullable=False, server_default="false")
    event_id = Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=True)
    profile_pic = Column(LargeBinary, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
