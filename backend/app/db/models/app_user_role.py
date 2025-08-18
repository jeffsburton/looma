from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class AppUserRole(Base):
    __tablename__ = "app_user_role"

    # Composite PK using app_user_id + role_id
    app_user_id = Column(Integer, ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)

    # Optional relationships
    # user = relationship("AppUser", backref="user_roles")
    # role = relationship("Role", backref="role_users")