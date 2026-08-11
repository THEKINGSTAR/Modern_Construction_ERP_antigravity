import uuid
from sqlalchemy import Column, String, ForeignKey, Uuid
from app.core.database import Base
from app.core.models import TenantAwareMixin

class Role(TenantAwareMixin, Base):
    __tablename__ = "roles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)


class Permission(Base):
    """
    Permissions are globally defined in the system code and seeded, 
    so they don't necessarily belong to a specific tenant.
    Examples: 'projects.read', 'finance.journal.post'
    """
    __tablename__ = "permissions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)


class UserRole(TenantAwareMixin, Base):
    __tablename__ = "user_roles"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)


class RolePermission(TenantAwareMixin, Base):
    __tablename__ = "role_permissions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_id = Column(ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False)
