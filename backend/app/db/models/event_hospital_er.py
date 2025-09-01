from sqlalchemy import Column, Integer, ForeignKey, Date, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class EventHospitalEr(Base):
    __tablename__ = "event_hospital_er"
    __table_args__ = (
        UniqueConstraint("event_id", "hospital_er_id", name="uq_event_hospital_er"),
    )

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id", ondelete="CASCADE"), nullable=False)
    hospital_er_id = Column(Integer, ForeignKey("hospital_er.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
