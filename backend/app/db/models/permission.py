from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base, TimestampMixin


class Permission(Base, TimestampMixin):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    code = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    parent_id = Column(Integer, ForeignKey("permission.id", ondelete="SET NULL"), nullable=True)

    # Relationships (self-referential)
    parent = relationship("Permission", remote_side=[id], backref="children", passive_deletes=True)

    # roles = relationship(
    #     "Role",
    #     secondary="role_permission",
    #     back_populates="permissions",
    # )
