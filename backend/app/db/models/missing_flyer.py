from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Date, String, Time
from sqlalchemy.sql import func

from app.db import Base


class MissingFlyer(Base):
    __tablename__ = "missing_flyer"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    created_by = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)



    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
