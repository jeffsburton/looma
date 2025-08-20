from sqlalchemy import Column, Integer, String

from app.db import Base


class RefPerRelation(Base):
    __tablename__ = "ref_per_relation"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
