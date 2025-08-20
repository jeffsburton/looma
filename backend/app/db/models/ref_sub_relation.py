from sqlalchemy import Column, Integer, String

from app.db import Base


class RefSubRelation(Base):
    __tablename__ = "ref_sub_relation"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(50), nullable=True)
