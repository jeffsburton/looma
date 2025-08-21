from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, Text
from sqlalchemy.sql import func

from app.db import Base


class PreviousRun(Base):
    __tablename__ = "previous_run"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    date_ran = Column(Date, nullable=False)
    point_last_seen = Column(Text, nullable=True)
    accompanied_by = Column(Text, nullable=True)
    found_by = Column(Text, nullable=True)
    date_found = Column(Date, nullable=True)
    location_found = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)


    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
