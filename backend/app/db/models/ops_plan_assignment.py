from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class OpsPlanAssignement(Base):
    __tablename__ = "ops_plan_assignment"
    __table_args__ = (
        UniqueConstraint("ops_plan_id", "person_id", name="uq_ops_plan_person"),
    )

    id = Column(Integer, primary_key=True, index=True)
    ops_plan_id = Column(Integer, ForeignKey("ops_plan.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)

    # ref_type OP_ROLE
    role_id = Column(Integer, ForeignKey("ref_value.id", ondelete="CASCADE"), nullable=False)
    role_other = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
