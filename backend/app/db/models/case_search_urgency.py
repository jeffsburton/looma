
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class CaseSearchUrgency(Base):
    __tablename__ = "case_search_urgency"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False, unique=True)

    # ref_type SU_AGE
    age_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type SU_FIT
    physical_condition_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type SU_MED
    medical_condition_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type SU_RISK
    personal_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type SU_ONL
    online_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type SU_FAM
    family_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    #ref_type SU_BE
    behavioral_risk_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    score = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)