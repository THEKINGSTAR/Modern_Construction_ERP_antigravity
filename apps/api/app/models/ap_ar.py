import uuid
import enum
from decimal import Decimal
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

class MatchingStatus(str, enum.Enum):
    UNMATCHED = "UNMATCHED"
    MATCHED = "MATCHED"
    VARIANCE = "VARIANCE"
    MANUALLY_APPROVED = "MANUALLY_APPROVED"

class APInvoice(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ap_invoices"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(100), nullable=False)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    purchase_order_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_orders.id"), nullable=True)
    goods_receipt_id = Column(Uuid(as_uuid=True), ForeignKey("goods_receipts.id"), nullable=True)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus, native_enum=False), default=InvoiceStatus.DRAFT, nullable=False)
    invoice_type = Column(Enum(InvoiceType, native_enum=False), default=InvoiceType.STANDARD, nullable=False)
    matching_status = Column(String(50), default="UNMATCHED", nullable=False)
    subtotal = Column(Numeric(18, 4), default=0.0, nullable=False)
    tax_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    total_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    currency = Column(String(3), default="USD")
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id"), nullable=True)
    description = Column(Text, nullable=True)

    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id])
    goods_receipt = relationship("GoodsReceipt", foreign_keys=[goods_receipt_id])
    journal = relationship("Journal", foreign_keys=[journal_id])
    lines = relationship("APInvoiceLine", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")
    allocations = relationship("PaymentAllocation", foreign_keys="[PaymentAllocation.ap_invoice_id]", back_populates="ap_invoice", lazy="selectin")

    @property
    def supplier_name(self) -> str | None:
        return self.supplier.name if self.supplier else None

    @property
    def po_number(self) -> str | None:
        return self.purchase_order.po_number if self.purchase_order else None

    @property
    def grn_number(self) -> str | None:
        return self.goods_receipt.receipt_number if self.goods_receipt else None

    @property
    def lines_count(self) -> int:
        return len(self.lines) if self.lines else 0

    @property
    def paid_amount(self) -> Decimal:
        if not self.allocations:
            return Decimal("0.0000")
        return sum((Decimal(str(a.amount)) for a in self.allocations), Decimal("0.0000"))

    @property
    def outstanding_amount(self) -> Decimal:
        total = Decimal(str(self.total_amount)) if self.total_amount is not None else Decimal("0.0000")
        return max(Decimal("0.0000"), total - self.paid_amount)

class APInvoiceLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ap_invoice_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ap_invoices.id"), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id"), nullable=True)
    purchase_order_line_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_order_lines.id"), nullable=True)
    goods_receipt_line_id = Column(Uuid(as_uuid=True), ForeignKey("goods_receipt_lines.id"), nullable=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(18, 4), default=1.0)
    unit_price = Column(Numeric(18, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    tax_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    line_total = Column(Numeric(18, 4), nullable=False)

    invoice = relationship("APInvoice", back_populates="lines")
    project = relationship("Project", foreign_keys=[project_id])
    cost_code = relationship("CostCode", foreign_keys=[cost_code_id])
    purchase_order_line = relationship("PurchaseOrderLine", foreign_keys=[purchase_order_line_id])
    goods_receipt_line = relationship("GoodsReceiptLine", foreign_keys=[goods_receipt_line_id])
    material = relationship("Material", foreign_keys=[material_id])

    @property
    def material_code(self) -> str | None:
        return self.material.material_code if self.material else None

    @property
    def material_name(self) -> str | None:
        return self.material.name if self.material else None

    @property
    def project_name(self) -> str | None:
        return self.project.name if self.project else None

    @property
    def cost_code_code(self) -> str | None:
        return self.cost_code.code if self.cost_code else None

class ARInvoice(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ar_invoices"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String(100), nullable=False)
    client_id = Column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False)
    contract_id = Column(Uuid(as_uuid=True), ForeignKey("contracts.id"), nullable=True)
    payment_application_id = Column(Uuid(as_uuid=True), ForeignKey("client_payment_applications.id"), nullable=True)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus, native_enum=False), default=InvoiceStatus.DRAFT, nullable=False)
    invoice_type = Column(Enum(InvoiceType, native_enum=False), default=InvoiceType.STANDARD, nullable=False)
    subtotal = Column(Numeric(18, 4), default=0.0, nullable=False)
    tax_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    retention_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    total_amount = Column(Numeric(18, 4), default=0.0, nullable=False)
    currency = Column(String(3), default="USD")
    journal_id = Column(Uuid(as_uuid=True), ForeignKey("journals.id"), nullable=True)
    description = Column(Text, nullable=True)

    client = relationship("Client", foreign_keys=[client_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    payment_application = relationship("ClientPaymentApplication", foreign_keys=[payment_application_id])
    journal = relationship("Journal", foreign_keys=[journal_id])
    lines = relationship("ARInvoiceLine", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")
    allocations = relationship("PaymentAllocation", foreign_keys="[PaymentAllocation.ar_invoice_id]", back_populates="ar_invoice", lazy="selectin")

    @property
    def client_name(self):
        return self.client.name if self.client else None

    @property
    def contract_number(self):
        return self.contract.contract_number if self.contract else None

    @property
    def payment_application_number(self):
        return self.payment_application.number if self.payment_application else None

    @property
    def lines_count(self):
        return len(self.lines) if self.lines else 0

    @property
    def paid_amount(self):
        if not self.allocations:
            return Decimal("0.00")
        return sum(
            Decimal(str(a.amount))
            for a in self.allocations
            if a.payment and a.payment.status == PaymentStatus.POSTED
        )

    @property
    def outstanding_amount(self):
        paid = self.paid_amount
        total = Decimal(str(self.total_amount or 0))
        return max(Decimal("0.00"), total - paid)

class ARInvoiceLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "ar_invoice_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(Uuid(as_uuid=True), ForeignKey("ar_invoices.id"), nullable=False)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id"), nullable=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(18, 4), default=1.0)
    unit_price = Column(Numeric(18, 4), nullable=False)
    line_total = Column(Numeric(18, 4), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.0, nullable=False)
    tax_amount = Column(Numeric(18, 4), default=0.0, nullable=False)

    invoice = relationship("ARInvoice", back_populates="lines")
    project = relationship("Project", foreign_keys=[project_id])
    cost_code = relationship("CostCode", foreign_keys=[cost_code_id])

    @property
    def project_name(self):
        return self.project.name if self.project else None

    @property
    def cost_code_code(self):
        return self.cost_code.code if self.cost_code else None

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

    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    client = relationship("Client", foreign_keys=[client_id])
    bank_account = relationship("BankAccount", foreign_keys=[bank_account_id])
    journal = relationship("Journal", foreign_keys=[journal_id])
    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan", lazy="selectin")
    bank_transaction = relationship("BankTransaction", back_populates="payment", uselist=False)

    @property
    def supplier_name(self) -> str | None:
        return self.supplier.name if self.supplier else None

    @property
    def client_name(self) -> str | None:
        return self.client.name if self.client else None

    @property
    def bank_name(self) -> str | None:
        return self.bank_account.bank_name if self.bank_account else None

    @property
    def bank_account_name(self) -> str | None:
        return self.bank_account.name if self.bank_account else None

    @property
    def allocations_count(self) -> int:
        return len(self.allocations) if self.allocations else 0

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
