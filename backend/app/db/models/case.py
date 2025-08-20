from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Case(Base):
    __tablename__ = "case"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subject.id"), nullable=False)
    date_missing = Column(Date, nullable=True)
    time_missing = Column(Time, nullable=True)
    number = Column(String(120), nullable=True)
    missing_from_state_id = Column(Integer, ForeignKey("ref_state.id"), nullable=True)
    inactive = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
