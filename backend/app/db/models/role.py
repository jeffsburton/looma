from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db import Base, TimestampMixin


class Role(Base, TimestampMixin):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True, index=True)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Relationships (optional, useful for ORM usage)
    # users = relationship(
    #     "AppUser",
    #     secondary="app_user_role",
    #     back_populates="roles",
    # )
    # permissions = relationship(
    #     "Permission",
    #     secondary="role_permission",
    #     back_populates="roles",
    # )
