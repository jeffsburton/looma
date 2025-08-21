from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class SubjectCase(Base):
    __tablename__ = "subject_case"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    relationship_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    relationship_other = Column(String(255), nullable=True)
    legal_guardian = Column(Boolean, nullable=False, server_default="false")
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
