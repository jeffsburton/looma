from sqlalchemy import Column, Integer, String

from app.db import Base


class RefState(Base):
    __tablename__ = "ref_state"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(20), nullable=False, unique=True, index=True)
