from sqlalchemy import Column, Integer, String

from app.db import Base


class RefActivity(Base):
    __tablename__ = "ref_activity"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
