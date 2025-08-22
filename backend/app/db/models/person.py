from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, LargeBinary
from sqlalchemy.sql import func

from app.db import Base


class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(120), nullable=False)
    last_name = Column(String(120), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    telegram = Column(String(50), nullable=True)
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=True)
    profile_pic = Column(LargeBinary, nullable=True)
    app_user_id = Column(Integer, ForeignKey("app_user.id"), nullable=True)




    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
