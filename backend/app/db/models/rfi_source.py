from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DateTime, Boolean
from sqlalchemy.sql import func

from app.db import Base


class RfiSource(Base):
    __tablename__ = "rfi_source"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    primary_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    backup_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    inactive = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
