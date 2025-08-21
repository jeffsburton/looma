
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class CaseSearchUrgency(Base):
    __tablename__ = "case_search_urgency"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    age_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    physical_condition_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    medical_condition_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    personal_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    online_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    family_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    behavioral_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)