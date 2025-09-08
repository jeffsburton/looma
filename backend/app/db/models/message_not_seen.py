from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, UniqueConstraint, String
from sqlalchemy.sql import func

from app.db import Base


class MessageNotSeen(Base):
    __tablename__ = "message_not_seen"
    __table_args__ = (
        UniqueConstraint('message_id', 'person_id', name='uq_message_person_not_seen'),
    )

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
