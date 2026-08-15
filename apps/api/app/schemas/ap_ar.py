from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from app.models.ap_ar import InvoiceStatus, InvoiceType, PaymentType, PaymentStatus

# AP Invoice
class APInvoiceLineBase(BaseModel):
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    description: str
    quantity: Decimal = Field(default=1.0, max_digits=18, decimal_places=4)
    unit_price: Decimal = Field(..., max_digits=18, decimal_places=4)

class APInvoiceLineCreate(APInvoiceLineBase):
    pass

class APInvoiceLineResponse(APInvoiceLineBase):
    id: UUID
    invoice_id: UUID
    line_total: Decimal = Field(..., max_digits=18, decimal_places=4)
    
    class Config:
        from_attributes = True

class APInvoiceBase(BaseModel):
    number: str = Field(..., max_length=100)
    supplier_id: UUID
    date: date
    due_date: date
    invoice_type: InvoiceType = InvoiceType.STANDARD
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None

class APInvoiceCreate(APInvoiceBase):
    lines: List[APInvoiceLineCreate]

class APInvoiceResponse(APInvoiceBase):
    id: UUID
    status: InvoiceStatus
    total_amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    journal_id: Optional[UUID] = None
    lines: List[APInvoiceLineResponse]
    outstanding_balance: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

# AR Invoice
class ARInvoiceLineBase(BaseModel):
    project_id: Optional[UUID] = None
    description: str
    quantity: Decimal = Field(default=1.0, max_digits=18, decimal_places=4)
    unit_price: Decimal = Field(..., max_digits=18, decimal_places=4)

class ARInvoiceLineCreate(ARInvoiceLineBase):
    pass

class ARInvoiceLineResponse(ARInvoiceLineBase):
    id: UUID
    invoice_id: UUID
    line_total: Decimal = Field(..., max_digits=18, decimal_places=4)
    
    class Config:
        from_attributes = True

class ARInvoiceBase(BaseModel):
    number: str = Field(..., max_length=100)
    client_id: UUID
    date: date
    due_date: date
    invoice_type: InvoiceType = InvoiceType.STANDARD
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None

class ARInvoiceCreate(ARInvoiceBase):
    lines: List[ARInvoiceLineCreate]

class ARInvoiceResponse(ARInvoiceBase):
    id: UUID
    status: InvoiceStatus
    total_amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    journal_id: Optional[UUID] = None
    lines: List[ARInvoiceLineResponse]
    outstanding_balance: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True
