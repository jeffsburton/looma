from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class HospitalEr(Base):
    __tablename__ = "hospital_er"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(200), nullable=False)
    city = Column(String(50), nullable=False)
    state_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    zip_code = Column(String(20), nullable=False)
    phone = Column(String(30), nullable=False)

    inactive = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
