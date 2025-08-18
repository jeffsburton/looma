from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class RolePermission(Base):
    __tablename__ = "role_permission"

    # Composite PK using role_id + permission_id
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.id"), primary_key=True)

    # Optional relationships for ORM use
    # role = relationship("Role", backref="role_permissions")
    # permission = relationship("Permission", backref="permission_roles")
