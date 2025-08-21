from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class File(Base):
    __tablename__ = "image"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    file_name = Column(String(255), nullable=False)
    created_by_id = Column(Integer, ForeignKey("person.id", ondelete="SET NULL"), nullable=True)
    source_url = Column(String(255), nullable=True)
    where = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    storage_slug = Column(String(100), nullable=True)

    rfi_id = Column(Integer, ForeignKey("rfi.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
