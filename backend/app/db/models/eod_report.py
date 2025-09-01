from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, DateTime, Text
from sqlalchemy.sql import func

from app.db import Base


class EodReport(Base):
    __tablename__ = "eod_report"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False, server_default=func.now())
    activity = Column(Text, nullable=True)
    communication = Column(Text, nullable=True)
    tomorrow_intel = Column(Text, nullable=True)
    tomorrow_ops = Column(Text, nullable=True)

    are_there_ministry_needs = Column(Boolean, nullable=False, server_default="false")
    ministry_needs = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
