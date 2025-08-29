from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from app.db import Base


class RefValue(Base):
    __tablename__ = "ref_value"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    description = Column(String(200), nullable=False, server_default="")
    code = Column(String(50), nullable=False)
    inactive = Column(Boolean, nullable=False, server_default="false")
    num_value = Column(Integer, nullable=True)
    sort_order = Column(Integer, nullable=True, index=True)
    ref_type_id = Column(Integer, ForeignKey("ref_type.id", ondelete="CASCADE"), nullable=False)