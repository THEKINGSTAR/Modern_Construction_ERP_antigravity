from pydantic import BaseModel, UUID4, Field
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.inventory import TransactionType

class InventoryBalanceResponse(BaseModel):
    id: UUID4
    warehouse_id: UUID4
    material_id: UUID4
    quantity: Decimal
    total_cost: Decimal
    
    class Config:
        from_attributes = True

class GoodsReceiptLineCreate(BaseModel):
    purchase_order_line_id: UUID4
    material_id: UUID4
    received_quantity: Decimal
    accepted_quantity: Decimal
    rejected_quantity: Decimal
    unit_cost: Decimal
    notes: Optional[str] = None

class GoodsReceiptCreate(BaseModel):
    receipt_number: str
    purchase_order_id: UUID4
    supplier_id: UUID4
    warehouse_id: UUID4
    date: date
    notes: Optional[str] = None
    lines: List[GoodsReceiptLineCreate]

class GoodsReceiptResponse(BaseModel):
    id: UUID4
    receipt_number: str
    status: str
    
    class Config:
        from_attributes = True

class MaterialIssueLineCreate(BaseModel):
    material_id: UUID4
    quantity: Decimal
    notes: Optional[str] = None

class MaterialIssueCreate(BaseModel):
    issue_number: str
    warehouse_id: UUID4
    project_id: UUID4
    cost_code_id: UUID4
    date: date
    purpose: Optional[str] = None
    requested_by_id: Optional[UUID4] = None
    lines: List[MaterialIssueLineCreate]

class MaterialIssueResponse(BaseModel):
    id: UUID4
    issue_number: str
    status: str
    
    class Config:
        from_attributes = True
