import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Date, Numeric, Text, Boolean, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class QuotationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EVALUATED = "EVALUATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class SupplierQuotation(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "supplier_quotations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(Uuid(as_uuid=True), ForeignKey("rfqs.id"), nullable=False)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    quotation_reference = Column(String(100), nullable=True)
    status = Column(Enum(QuotationStatus, native_enum=False), default=QuotationStatus.DRAFT, nullable=False)
    valid_until = Column(Date, nullable=True)
    currency = Column(String(3), nullable=True)
    notes = Column(Text, nullable=True)

    rfq = relationship("RFQ")
    supplier = relationship("Supplier")
    lines = relationship("SupplierQuotationLine", back_populates="quotation", cascade="all, delete-orphan")


class SupplierQuotationLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "supplier_quotation_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(Uuid(as_uuid=True), ForeignKey("supplier_quotations.id"), nullable=False)
    rfq_line_id = Column(Uuid(as_uuid=True), ForeignKey("rfq_lines.id"), nullable=False)
    unit_price = Column(Numeric(18, 4), nullable=False)
    quoted_quantity = Column(Numeric(18, 4), nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    lead_time_days = Column(Numeric(10, 0), nullable=True)
    is_selected = Column(Boolean, default=False)

    quotation = relationship("SupplierQuotation", back_populates="lines")
    rfq_line = relationship("RFQLine")
