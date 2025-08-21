
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class CasePatternOfLife(Base):
    __tablename__ = "case_pattern_of_life"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    school = Column(String(100), nullable=True)
    grade = Column(String(20), nullable=True)
    missing_classes = Column(Boolean, server_default="false", nullable=False)
    school_laptop = Column(Boolean, server_default="false", nullable=False)
    school_laptop_taken = Column(Boolean, server_default="false", nullable=False)

    school_address = Column(Text, nullable=True)

    employed = Column(Boolean, server_default="false", nullable=False)
    employer = Column(Text, nullable=True)
    work_hours = Column(Text, nullable=True)
    employer_address = Column(Text, nullable=True)

    confidants = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)