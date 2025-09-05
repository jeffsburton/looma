from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, UniqueConstraint, String
from sqlalchemy.sql import func

from app.db import Base


class MessagePerson(Base):
    __tablename__ = "message_person"
    __table_args__ = (
        UniqueConstraint('message_id', 'person_id', name='uq_message_person'),
    )

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)

    # reaction emoji
    reaction = Column(String(10), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
