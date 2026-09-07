from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, ConfigDict
from app.models.quotations import QuotationStatus

class SupplierQuotationLineBase(BaseModel):
    rfq_line_id: UUID
    unit_price: Decimal
    quoted_quantity: Decimal
    amount: Decimal
    lead_time_days: Optional[int] = None
    is_selected: bool = False

class SupplierQuotationLineCreate(SupplierQuotationLineBase):
    pass

class SupplierQuotationLineResponse(SupplierQuotationLineBase):
    id: UUID
    quotation_id: UUID
    model_config = ConfigDict(from_attributes=True)

class SupplierQuotationBase(BaseModel):
    rfq_id: UUID
    supplier_id: UUID
    quotation_reference: Optional[str] = None
    status: QuotationStatus = QuotationStatus.DRAFT
    valid_until: Optional[date] = None
    currency: Optional[str] = None
    notes: Optional[str] = None

class SupplierQuotationCreate(SupplierQuotationBase):
    lines: List[SupplierQuotationLineCreate]

class SupplierQuotationResponse(SupplierQuotationBase):
    id: UUID
    supplier_name: Optional[str] = None
    rfq_title: Optional[str] = None
    total_amount: Optional[Decimal] = None
    lines: List[SupplierQuotationLineResponse] = []
    model_config = ConfigDict(from_attributes=True)
