from sqlalchemy import Column, Integer, String, DateTime, Boolean, LargeBinary
from sqlalchemy.sql import func

from app.db import Base


class Subject(Base):
    __tablename__ = "subject"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    middle_name = Column(String(120), nullable=True)
    nicknames = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    dangerous = Column(Boolean, nullable=False, server_default="false")
    danger = Column(String(255), nullable=True)
    profile_pic = Column(LargeBinary, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
