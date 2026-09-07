import uuid
import enum
from sqlalchemy import Column, String, Uuid, Numeric, Date, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class ChangeOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class PaymentAppStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    PAID = "PAID"

class Subcontract(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "subcontracts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False)
    subcontract_number = Column(String(100), nullable=False)
    
    original_value = Column(Numeric(18, 6), default=0.0, nullable=False)
    current_value = Column(Numeric(18, 6), default=0.0, nullable=False)
    currency_code = Column(String(3), ForeignKey("currencies.code", ondelete="RESTRICT"), nullable=False)
    
    retention_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    project = relationship("Project")
    supplier = relationship("Supplier")

    @property
    def project_name(self):
        return self.project.name if self.project else None

    @property
    def supplier_name(self):
        return self.supplier.name if self.supplier else None

class ClientChangeOrder(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "client_change_orders"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(Uuid(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    number = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    
    amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    status = Column(Enum(ChangeOrderStatus, name="change_order_status_enum", create_type=False), default=ChangeOrderStatus.DRAFT, nullable=False)
    approved_date = Column(Date, nullable=True)
    
    contract = relationship("Contract")

    @property
    def contract_number(self):
        return self.contract.contract_number if self.contract else None

class SubcontractChangeOrder(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "subcontract_change_orders"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subcontract_id = Column(Uuid(as_uuid=True), ForeignKey("subcontracts.id", ondelete="CASCADE"), nullable=False)
    number = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    
    amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    status = Column(Enum(ChangeOrderStatus, name="sc_change_order_status_enum", create_type=False), default=ChangeOrderStatus.DRAFT, nullable=False)
    approved_date = Column(Date, nullable=True)
    
    subcontract = relationship("Subcontract")

    @property
    def subcontract_number(self):
        return self.subcontract.subcontract_number if self.subcontract else None

class ClientPaymentApplication(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "client_payment_applications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(Uuid(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    accounting_period_id = Column(Uuid(as_uuid=True), ForeignKey("accounting_periods.id", ondelete="RESTRICT"), nullable=False)
    number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    
    gross_work = Column(Numeric(18, 6), default=0.0, nullable=False)
    previous_certified_work = Column(Numeric(18, 6), default=0.0, nullable=False)
    retention_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    advance_recovery_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    deductions_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    adjustments_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    net_amount_due = Column(Numeric(18, 6), default=0.0, nullable=False)
    
    status = Column(Enum(PaymentAppStatus, name="payment_app_status_enum", create_type=False), default=PaymentAppStatus.DRAFT, nullable=False)
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id", ondelete="SET NULL"), nullable=True)
    
    contract = relationship("Contract")
    accounting_period = relationship("AccountingPeriod")
    journal = relationship("Journal")

    @property
    def contract_number(self):
        return self.contract.contract_number if self.contract else None

    @property
    def period_name(self):
        return self.accounting_period.name if self.accounting_period else None

class SubcontractPaymentApplication(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "subcontract_payment_applications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subcontract_id = Column(Uuid(as_uuid=True), ForeignKey("subcontracts.id", ondelete="CASCADE"), nullable=False)
    accounting_period_id = Column(Uuid(as_uuid=True), ForeignKey("accounting_periods.id", ondelete="RESTRICT"), nullable=False)
    number = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    
    gross_work = Column(Numeric(18, 6), default=0.0, nullable=False)
    previous_certified_work = Column(Numeric(18, 6), default=0.0, nullable=False)
    retention_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    advance_recovery_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    deductions_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    adjustments_amount = Column(Numeric(18, 6), default=0.0, nullable=False)
    net_amount_due = Column(Numeric(18, 6), default=0.0, nullable=False)
    
    status = Column(Enum(PaymentAppStatus, name="sc_payment_app_status_enum", create_type=False), default=PaymentAppStatus.DRAFT, nullable=False)
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id", ondelete="SET NULL"), nullable=True)
    
    subcontract = relationship("Subcontract")
    accounting_period = relationship("AccountingPeriod")
    journal = relationship("Journal")

    @property
    def subcontract_number(self):
        return self.subcontract.subcontract_number if self.subcontract else None

    @property
    def period_name(self):
        return self.accounting_period.name if self.accounting_period else None
