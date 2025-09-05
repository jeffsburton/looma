from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.sql import func

from app.db import Base


class Tasl(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    assigned_by_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    response = Column(Text, nullable=True)

    ready_for_review = Column(Boolean, nullable=False, server_default="false")

    completed = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
