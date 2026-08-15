import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    VOID = "VOID"

class InvoiceType(str, enum.Enum):
    STANDARD = "STANDARD"
    CREDIT_NOTE = "CREDIT_NOTE"

class APInvoice(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ap_invoices"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(100), nullable=False)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus, native_enum=False), default=InvoiceStatus.DRAFT, nullable=False)
    invoice_type = Column(Enum(InvoiceType, native_enum=False), default=InvoiceType.STANDARD, nullable=False)
    total_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    currency = Column(String(3), default="USD")
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id"), nullable=True)
    description = Column(Text, nullable=True)

    supplier = relationship("Supplier")
    journal = relationship("Journal")
    lines = relationship("APInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", foreign_keys="[PaymentAllocation.ap_invoice_id]", back_populates="ap_invoice")

class APInvoiceLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ap_invoice_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ap_invoices.id"), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(18, 4), default=1.0)
    unit_price = Column(Numeric(18, 4), nullable=False)
    line_total = Column(Numeric(18, 4), nullable=False)

    invoice = relationship("APInvoice", back_populates="lines")
    project = relationship("Project")
    cost_code = relationship("CostCode")

class ARInvoice(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ar_invoices"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(100), nullable=False)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus, native_enum=False), default=InvoiceStatus.DRAFT, nullable=False)
    invoice_type = Column(Enum(InvoiceType, native_enum=False), default=InvoiceType.STANDARD, nullable=False)
    total_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    currency = Column(String(3), default="USD")
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id"), nullable=True)
    description = Column(Text, nullable=True)

    client = relationship("Client")
    journal = relationship("Journal")
    lines = relationship("ARInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("PaymentAllocation", foreign_keys="[PaymentAllocation.ar_invoice_id]", back_populates="ar_invoice")

class ARInvoiceLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ar_invoice_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(18, 4), default=1.0)
    unit_price = Column(Numeric(18, 4), nullable=False)
    line_total = Column(Numeric(18, 4), nullable=False)

    invoice = relationship("ARInvoice", back_populates="lines")
    project = relationship("Project")

class PaymentType(str, enum.Enum):
    AP_PAYMENT = "AP_PAYMENT"
    AR_RECEIPT = "AR_RECEIPT"

class PaymentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    VOID = "VOID"

class Payment(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "payments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference = Column(String(100), nullable=False)
    payment_type = Column(Enum(PaymentType, native_enum=False), nullable=False)
    date = Column(Date, nullable=False)
    amount = Column(Numeric(18, 4), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.DRAFT, nullable=False)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=True)
    bank_account_id = Column(Uuid(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id"), nullable=True)

    supplier = relationship("Supplier")
    client = relationship("Client")
    bank_account = relationship("BankAccount")
    journal = relationship("Journal")
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
    bank_transaction = relationship("BankTransaction", back_populates="payment", uselist=False)

class PaymentAllocation(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "payment_allocations"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(Uuid(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    ap_invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ap_invoices.id"), nullable=True)
    ar_invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=True)
    amount = Column(Numeric(18, 4), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    ap_invoice = relationship("APInvoice", foreign_keys=[ap_invoice_id], back_populates="allocations")
    ar_invoice = relationship("ARInvoice", foreign_keys=[ar_invoice_id], back_populates="allocations")

from app.models.bank import BankTransaction
BankTransaction.payment = relationship("Payment", back_populates="bank_transaction")
