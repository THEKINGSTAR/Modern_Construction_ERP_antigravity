from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from datetime import date
from uuid import UUID
from decimal import Decimal
from app.models.ap_ar import InvoiceStatus, InvoiceType, PaymentType, PaymentStatus, MatchingStatus

# AP Invoice Line
class APInvoiceLineBase(BaseModel):
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    purchase_order_line_id: Optional[UUID] = None
    goods_receipt_line_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    description: str
    quantity: Decimal = Field(default=1.0, max_digits=18, decimal_places=4)
    unit_price: Decimal = Field(..., max_digits=18, decimal_places=4)
    tax_rate: Decimal = Field(default=0.0, max_digits=5, decimal_places=2)
    tax_amount: Optional[Decimal] = Field(default=0.0, max_digits=18, decimal_places=4)

class APInvoiceLineCreate(APInvoiceLineBase):
    pass

class APInvoiceLineResponse(APInvoiceLineBase):
    id: UUID
    invoice_id: UUID
    line_total: Decimal = Field(..., max_digits=18, decimal_places=4)
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None
    
    class Config:
        from_attributes = True

# AP Invoice
class APInvoiceBase(BaseModel):
    number: str = Field(..., max_length=100)
    supplier_id: UUID
    purchase_order_id: Optional[UUID] = None
    goods_receipt_id: Optional[UUID] = None
    date: date
    due_date: date
    invoice_type: InvoiceType = InvoiceType.STANDARD
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None

class APInvoiceCreate(APInvoiceBase):
    lines: List[APInvoiceLineCreate]
    tax_amount: Optional[Decimal] = Field(default=0.0, max_digits=18, decimal_places=4)

class APInvoiceResponse(APInvoiceBase):
    id: UUID
    status: InvoiceStatus
    matching_status: str = "UNMATCHED"
    subtotal: Decimal = Field(default=0.0, max_digits=18, decimal_places=4)
    tax_amount: Decimal = Field(default=0.0, max_digits=18, decimal_places=4)
    total_amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    journal_id: Optional[UUID] = None
    lines: List[APInvoiceLineResponse]
    supplier_name: Optional[str] = None
    po_number: Optional[str] = None
    grn_number: Optional[str] = None
    lines_count: Optional[int] = 0
    paid_amount: Optional[Decimal] = None
    outstanding_amount: Optional[Decimal] = None
    outstanding_balance: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

# 3-Way Match Schemas
class ThreeWayMatchLineReport(BaseModel):
    invoice_line_id: UUID
    description: str
    invoice_qty: Decimal
    invoice_unit_price: Decimal
    invoice_line_total: Decimal
    po_qty: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    grn_accepted_qty: Optional[Decimal] = None
    qty_variance: Decimal
    price_variance: Decimal
    total_variance: Decimal
    line_status: str
    notes: Optional[str] = None

class ThreeWayMatchResponse(BaseModel):
    invoice_id: UUID
    invoice_number: str
    supplier_name: Optional[str] = None
    purchase_order_id: Optional[UUID] = None
    po_number: Optional[str] = None
    goods_receipt_id: Optional[UUID] = None
    grn_number: Optional[str] = None
    matching_status: str
    total_invoice_amount: Decimal
    total_po_amount: Optional[Decimal] = None
    total_grn_accepted_amount: Optional[Decimal] = None
    variance_amount: Decimal
    is_matched: bool
    can_approve: bool
    lines: List[ThreeWayMatchLineReport]

# AP Summary
class APSummaryResponse(BaseModel):
    total_payables: Decimal
    total_invoiced: Decimal
    total_paid: Decimal
    invoices_count: int
    draft_count: int
    approved_count: int
    posted_count: int
    paid_count: int
    matched_count: int
    variance_count: int
    aging_current: Decimal
    aging_31_60: Decimal
    aging_61_90: Decimal
    aging_over_90: Decimal
    recent_invoices: List[dict] = []
    recent_payments: List[dict] = []

# AR Invoice
class ARInvoiceLineBase(BaseModel):
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    description: str
    quantity: Decimal = Field(default=1.0, max_digits=18, decimal_places=4)
    unit_price: Decimal = Field(..., max_digits=18, decimal_places=4)
    tax_rate: Decimal = Field(default=Decimal("0.0"), max_digits=5, decimal_places=2)
    tax_amount: Decimal = Field(default=Decimal("0.0"), max_digits=18, decimal_places=4)

class ARInvoiceLineCreate(ARInvoiceLineBase):
    pass

class ARInvoiceLineResponse(ARInvoiceLineBase):
    id: UUID
    invoice_id: UUID
    line_total: Decimal = Field(..., max_digits=18, decimal_places=4)
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None
    
    class Config:
        from_attributes = True

class ARInvoiceBase(BaseModel):
    number: str = Field(..., max_length=100)
    client_id: UUID
    contract_id: Optional[UUID] = None
    payment_application_id: Optional[UUID] = None
    date: date
    due_date: date
    invoice_type: InvoiceType = InvoiceType.STANDARD
    subtotal: Optional[Decimal] = Field(default=Decimal("0.0"), max_digits=18, decimal_places=4)
    tax_amount: Optional[Decimal] = Field(default=Decimal("0.0"), max_digits=18, decimal_places=4)
    retention_amount: Optional[Decimal] = Field(default=Decimal("0.0"), max_digits=18, decimal_places=4)
    total_amount: Optional[Decimal] = Field(default=Decimal("0.0"), max_digits=18, decimal_places=4)
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None

class ARInvoiceCreate(ARInvoiceBase):
    lines: List[ARInvoiceLineCreate]

class ARInvoiceResponse(ARInvoiceBase):
    id: UUID
    status: InvoiceStatus
    journal_id: Optional[UUID] = None
    lines: List[ARInvoiceLineResponse]
    client_name: Optional[str] = None
    contract_number: Optional[str] = None
    payment_application_number: Optional[str] = None
    lines_count: Optional[int] = 0
    paid_amount: Optional[Decimal] = Decimal("0.0")
    outstanding_amount: Optional[Decimal] = Decimal("0.0")
    
    class Config:
        from_attributes = True

class ARSummaryResponse(BaseModel):
    total_invoiced: Decimal
    total_receivables: Decimal
    total_received: Decimal
    total_retention_held: Decimal
    invoices_count: int
    draft_count: int
    approved_count: int
    posted_count: int
    paid_count: int
    collections_count: int
    current_receivables: Decimal
    overdue_30: Decimal
    overdue_60: Decimal
    overdue_90_plus: Decimal
    recent_invoices: List[dict] = []
    recent_receipts: List[dict] = []

# Payments
class PaymentAllocationBase(BaseModel):
    ap_invoice_id: Optional[UUID] = None
    ar_invoice_id: Optional[UUID] = None
    amount: Decimal = Field(..., max_digits=18, decimal_places=4)

    @field_validator("ar_invoice_id")
    def check_one_invoice(cls, v, values):
        ap_id = values.data.get("ap_invoice_id")
        if (ap_id and v) or (not ap_id and not v):
            raise ValueError("Either ap_invoice_id or ar_invoice_id must be provided, but not both.")
        return v

class PaymentAllocationCreate(PaymentAllocationBase):
    pass

class PaymentAllocationResponse(PaymentAllocationBase):
    id: UUID
    payment_id: UUID
    
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    reference: str = Field(..., max_length=100)
    payment_type: PaymentType
    date: date
    amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    currency: str = Field(default="USD", max_length=3)
    supplier_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    bank_account_id: UUID

class PaymentCreate(PaymentBase):
    allocations: List[PaymentAllocationCreate] = []

class PaymentResponse(PaymentBase):
    id: UUID
    status: PaymentStatus
    journal_id: Optional[UUID] = None
    allocations: List[PaymentAllocationResponse]
    unapplied_amount: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    client_name: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    allocations_count: Optional[int] = 0
    
    class Config:
        from_attributes = True
