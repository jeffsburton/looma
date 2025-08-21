
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class victimology(Base):
    __tablename__ = "victimology"

    id = Column(Integer, primary_key=True, index=True)
    victimology_category_id = Column(Integer, ForeignKey("victimology.id", ondelete="CASCADE"), nullable=False)

    question = Column(Text, nullable=False)
    follow_up = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)