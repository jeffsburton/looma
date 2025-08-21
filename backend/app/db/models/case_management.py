
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean, Date
from sqlalchemy.sql import func

from app.db import Base


class CaseManagement(Base):
    __tablename__ = "case_management"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)


    consent_sent = Column(Boolean, server_default="false", nullable=False)
    consent_returned = Column(Boolean, server_default="false", nullable=False)
    flyer_complete = Column(Boolean, server_default="false", nullable=False)

    ottic = Column(Boolean, server_default="false", nullable=False)

    csec_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    missing_status_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    classification_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    ncic_case_number = Column(String(30), nullable=True)
    ncmec_case_number = Column(String(30), nullable=True)

    le_case_number = Column(String(30), nullable=True)
    le_24hour_contact = Column(String(30), nullable=True)
    ss_case_number = Column(String(30), nullable=True)
    ss_24hour_contact = Column(String(30), nullable=True)
    jpo_case_number = Column(String(30), nullable=True)
    jpo_24hour_contact = Column(String(30), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)