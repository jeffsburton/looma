
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean, Date
from sqlalchemy.sql import func

from app.db import Base


class CaseDemographics(Base):
    __tablename__ = "case_demographics"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    date_of_birth = Column(Date, nullable=True)
    age_when_missing = Column(Integer, nullable=True)
    height = Column(String(20), nullable=True)
    weight = Column(String(20), nullable=True)
    hair_color = Column(String(20), nullable=True)
    hair_length = Column(String(20), nullable=True)
    eye_color = Column(String(20), nullable=True)


    identifying_marks = Column(Text, nullable=True)

    sex_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)