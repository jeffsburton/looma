from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class PersonTeam(Base):
    __tablename__ = "person_team"
    __table_args__ = (
        UniqueConstraint("person_id", "team_id", name="uq_person_team"),
    )

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("person.id", ondelete="CASCADE"), nullable=False)
    team_id = Column(Integer, ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    team_role_id = Column(Integer, ForeignKey("ref_value.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
