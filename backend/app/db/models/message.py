from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    # who wrote the message.
    written_by_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)


    message = Column(Text, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("message.id", ondelete="SET NULL"), nullable=True)

    rfi_id = Column(Integer, ForeignKey("rfi.id", ondelete="SET NULL"), nullable=True)
    ops_plan_id = Column(Integer, ForeignKey("ops_plan.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(Integer, ForeignKey("task.id", ondelete="SET NULL"), nullable=True)

    file_id = Column(Integer, ForeignKey("file.id", ondelete="CASCADE"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
