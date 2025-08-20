from sqlalchemy import Column, Integer, String

from app.db import Base


class RefSmPlatform(Base):
    __tablename__ = "ref_sm_platform"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    url = Column(String(255), nullable=True)
