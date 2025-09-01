from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db import Base


class RolePermission(Base):
    __tablename__ = "role_permission"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    # Composite PK using role_id + permission_id
    role_id = Column(Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permission.id"), primary_key=True)

    # Optional relationships for ORM use
    # role = relationship("Role", backref="role_permissions")
    # permission = relationship("Permission", backref="permission_roles")
