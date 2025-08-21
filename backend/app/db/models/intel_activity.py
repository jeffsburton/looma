from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class IntelActivity(Base):
    __tablename__ = "intel_activity"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    entered_by_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    what = Column(Text, nullable=True)
    source_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    source_other = Column(String(255), nullable=True)
    findings = Column(Text, nullable=True)
    case_management = Column(Text, nullable=True)
    reported_to  = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=True)
    on_eod_report = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
