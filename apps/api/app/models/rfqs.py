import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Date, Numeric, Text, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class RFQStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class RFQ(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "rfqs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_number = Column(String(100), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    requisition_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(RFQStatus, native_enum=False), default=RFQStatus.DRAFT, nullable=False)
    due_date = Column(Date, nullable=True)

    project = relationship("Project")
    requisition = relationship("PurchaseRequisition")
    lines = relationship("RFQLine", back_populates="rfq", cascade="all, delete-orphan")
    @property
    def project_name(self):
        return self.project.name if self.project else None

    @property
    def requisition_number(self):
        return self.requisition.pr_number if self.requisition else None

    @property
    def lines_count(self):
        return len(self.lines) if self.lines else 0



class RFQLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "rfq_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rfq_id = Column(Uuid(as_uuid=True), ForeignKey("rfqs.id"), nullable=False)
    pr_line_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_requisition_lines.id"), nullable=True)
    item_description = Column(String(500), nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)

    rfq = relationship("RFQ", back_populates="lines")
    pr_line = relationship("PurchaseRequisitionLine")
