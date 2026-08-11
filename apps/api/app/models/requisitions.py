import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Date, Numeric, Text, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class PRStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class PurchaseRequisition(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "purchase_requisitions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_number = Column(String(100), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    requester_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(PRStatus, native_enum=False), default=PRStatus.DRAFT, nullable=False)
    required_date = Column(Date, nullable=True)

    project = relationship("Project")
    requester = relationship("User")
    lines = relationship("PurchaseRequisitionLine", back_populates="requisition", cascade="all, delete-orphan")


class PurchaseRequisitionLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "purchase_requisition_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requisition_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_requisitions.id"), nullable=False)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id"), nullable=True)
    item_description = Column(String(500), nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)

    requisition = relationship("PurchaseRequisition", back_populates="lines")
    cost_code = relationship("CostCode")
