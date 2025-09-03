from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Date, Time, Boolean
from sqlalchemy.sql import func

from app.db import Base


class Timeline(Base):
    __tablename__ = "timeline"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    entered_by_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=True)

    # ref_type TL_TYPE
    type_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    type_other = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    where = Column(Text, nullable=True)
    who_id = Column(Integer, ForeignKey("person.id", ondelete="SET NULL"), nullable=True)
    questions = Column(Text, nullable=True)

    rule_out = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
