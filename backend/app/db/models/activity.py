from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    source = Column(String(255), nullable=True)
    regarding_id = Column(Integer, ForeignKey("ref_activity.id"), nullable=True)
    findings = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
