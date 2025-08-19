from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Qualification(Base):
    __tablename__ = "qualification"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)