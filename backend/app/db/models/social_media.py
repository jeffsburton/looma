from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class SocialMedia(Base):
    __tablename__ = "social_media"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="SET NULL"), nullable=True)


    # ref_type SM_PLATFORM
    platform_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)
    platform_other = Column(Text, nullable=True)
    url = Column(Text, nullable=False)

    # ref_type SM_STAT
    status_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)

    # ref_type SM_INV
    investigated_id = Column(Integer, ForeignKey("ref_value.id"), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
