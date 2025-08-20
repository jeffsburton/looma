from sqlalchemy import Column, Integer, String

from app.db import Base


class RefFoundBy(Base):
    __tablename__ = "ref_found_by"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(50), nullable=True)
