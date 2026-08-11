import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class SupplierStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    BLACKLISTED = "BLACKLISTED"

class Supplier(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "suppliers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    tax_identifier = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    status = Column(Enum(SupplierStatus, native_enum=False), default=SupplierStatus.ACTIVE, nullable=False)

    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")

class SupplierContact(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "supplier_contacts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)

    supplier = relationship("Supplier", back_populates="contacts")
