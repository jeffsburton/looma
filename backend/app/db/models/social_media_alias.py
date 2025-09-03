from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func

from app.db import Base


class SocialMediaAlias(Base):
    __tablename__ = "social_media_alias"

    id = Column(Integer, primary_key=True, index=True)
    social_media_id = Column(Integer, ForeignKey("social_media.id", ondelete="CASCADE"), nullable=False)

    # ref_type SM_ALIAS
    alias_status_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)

    alias = Column(Text, nullable=True)

    # the shepherd who owns the alias
    alias_owner_id = Column(Integer, ForeignKey("person.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

