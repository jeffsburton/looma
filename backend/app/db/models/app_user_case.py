from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from app.db import Base


class AppUserCase(Base):
    __tablename__ = "app_user_case"
    __table_args__ = (
        UniqueConstraint("case_id", "app_user_id", name="uq_app_user_case_case_user"),
    )

    id = Column(Integer, primary_key=True, index=True)
    app_user_id = Column(Integer, ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    case_id = Column(Integer, ForeignKey("case.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
