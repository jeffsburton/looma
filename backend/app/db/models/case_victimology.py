
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class CaseVictimology(Base):
    __tablename__ = "case_victimology"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    victimology_id = Column(Integer, ForeignKey("victimology.id", ondelete="CASCADE"), nullable=False)

    answer_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)