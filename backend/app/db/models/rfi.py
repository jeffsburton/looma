from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class Rfi(Base):
    __tablename__ = "rfi"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(255), nullable=False)

    created_by = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    # ref_type
    rfi_source_id = Column(Integer, ForeignKey("rfi_source.id", ondelete="CASCADE"), nullable=False)

    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False)

    details = Column(Text, nullable=True)

    responded_by_id = Column(Integer, ForeignKey("person.id", ondelete="SET NULL"), nullable=True)

    results = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
