
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text, String, Boolean
from sqlalchemy.sql import func

from app.db import Base


class victimologyCategory(Base):
    __tablename__ = "victimology_category"

    id = Column(Integer, primary_key=True, index=True)

    category = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)