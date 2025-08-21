from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func

from app.db import Base


class CaseAction(Base):
    __tablename__ = "case_action"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    action_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
