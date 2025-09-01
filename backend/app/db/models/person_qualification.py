from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class PersonQualification(Base):
    __tablename__ = "person_qualification"
    __table_args__ = (
        UniqueConstraint("person_id", "qualification_id", name="uq_person_qualification"),
    )

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    qualification_id = Column(Integer, ForeignKey("qualification.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
