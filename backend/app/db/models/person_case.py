from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, UniqueConstraint, Boolean
from sqlalchemy.sql import func

from app.db import Base


class PersonCase(Base):
    __tablename__ = "person_case"
    __table_args__ = (
        UniqueConstraint("person_id", "case_id", name="uq_person_case"),
    )

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    # ref_type PER_REL
    relationship_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)
    relationship_other = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
