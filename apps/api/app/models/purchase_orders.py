import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Date, Numeric, Text, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class POStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PurchaseOrder(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "purchase_orders"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    po_number = Column(String(100), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    quotation_id = Column(Uuid(as_uuid=True), ForeignKey("supplier_quotations.id"), nullable=True)
    status = Column(Enum(POStatus, native_enum=False), default=POStatus.DRAFT, nullable=False)
    issue_date = Column(Date, nullable=True)
    delivery_date = Column(Date, nullable=True)
    total_amount = Column(Numeric(18, 4), default=0, nullable=False)
    currency = Column(String(3), nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project")
    supplier = relationship("Supplier")
    quotation = relationship("SupplierQuotation")
    lines = relationship("PurchaseOrderLine", back_populates="purchase_order", cascade="all, delete-orphan")
    @property
    def project_name(self):
        return self.project.name if self.project else None

    @property
    def supplier_name(self):
        return self.supplier.name if self.supplier else None



class PurchaseOrderLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "purchase_order_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    purchase_order_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=False)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id"), nullable=True)
    item_description = Column(String(500), nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)

    purchase_order = relationship("PurchaseOrder", back_populates="lines")
    cost_code = relationship("CostCode")
