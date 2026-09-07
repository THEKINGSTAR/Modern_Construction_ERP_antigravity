from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, ConfigDict
from app.models.purchase_orders import POStatus

class PurchaseOrderLineBase(BaseModel):
    cost_code_id: Optional[UUID] = None
    item_description: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal

class PurchaseOrderLineCreate(PurchaseOrderLineBase):
    pass

class PurchaseOrderLineResponse(PurchaseOrderLineBase):
    id: UUID
    purchase_order_id: UUID
    model_config = ConfigDict(from_attributes=True)

class PurchaseOrderBase(BaseModel):
    po_number: str
    project_id: Optional[UUID] = None
    supplier_id: UUID
    quotation_id: Optional[UUID] = None
    status: POStatus = POStatus.DRAFT
    issue_date: Optional[date] = None
    delivery_date: Optional[date] = None
    total_amount: Decimal = Decimal('0.0000')
    currency: Optional[str] = None
    notes: Optional[str] = None

class PurchaseOrderCreate(PurchaseOrderBase):
    lines: List[PurchaseOrderLineCreate]

class PurchaseOrderResponse(PurchaseOrderBase):
    id: UUID
    supplier_name: Optional[str] = None
    project_name: Optional[str] = None
    lines: List[PurchaseOrderLineResponse] = []
    model_config = ConfigDict(from_attributes=True)

class ProcurementSummaryResponse(BaseModel):
    total_po_value: Decimal = Decimal('0.0000')
    active_pos_count: int = 0
    pending_requisitions_count: int = 0
    approved_suppliers_count: int = 0
    total_suppliers_count: int = 0
    recent_pos: List[PurchaseOrderResponse] = []
