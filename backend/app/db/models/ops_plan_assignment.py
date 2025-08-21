from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, String
from sqlalchemy.sql import func

from app.db import Base


class OpsPlanAssignement(Base):
    __tablename__ = "ops_plan_assignment"

    id = Column(Integer, primary_key=True, index=True)
    ops_plan_id = Column(Integer, ForeignKey("ops_plan.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=False)
    role_other = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
