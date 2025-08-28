from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(200), nullable=False)
    city = Column(String(200), nullable=False, server_default="")
    state_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    start = Column(Date, nullable=True)
    end = Column(Date, nullable=True)
    inactive = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
