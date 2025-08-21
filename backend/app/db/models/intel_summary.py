from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class IntelSummary(Base):
    __tablename__ = "intel_summary"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    date = Column(Date, nullable=False)
    entered_by_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
