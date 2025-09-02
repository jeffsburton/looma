from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Boolean, DateTime
from sqlalchemy.sql import func

from app.db import Base


class CaseDisposition(Base):
    __tablename__ = "case_disposition"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False, unique=True)
    shepherds_contributed_intel = Column(Boolean, nullable=False, server_default="false")
    date_found = Column(Date, nullable=True)

    # ref_type SCOPE
    scope_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type CASE_CLASS
    class_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type STATUS
    status_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type LIVING
    living_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    # ref_type FOUND_BY
    found_by_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
