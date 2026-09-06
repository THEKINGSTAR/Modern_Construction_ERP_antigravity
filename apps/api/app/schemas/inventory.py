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

class InventoryTransferLineCreate(BaseModel):
    material_id: UUID4
    quantity: Decimal
    notes: Optional[str] = None

class InventoryTransferCreate(BaseModel):
    transfer_number: str
    source_warehouse_id: UUID4
    destination_warehouse_id: UUID4
    date: date
    notes: Optional[str] = None
    lines: List[InventoryTransferLineCreate]

class InventoryTransferResponse(BaseModel):
    id: UUID4
    transfer_number: str
    status: str

    class Config:
        from_attributes = True

from app.models.inventory_adjustments import AdjustmentType

class InventoryAdjustmentLineCreate(BaseModel):
    material_id: UUID4
    adjustment_type: AdjustmentType
    quantity: Decimal
    unit_cost: Decimal
    notes: Optional[str] = None

class InventoryAdjustmentCreate(BaseModel):
    adjustment_number: str
    warehouse_id: UUID4
    date: date
    reason: Optional[str] = None
    lines: List[InventoryAdjustmentLineCreate]

class InventoryAdjustmentResponse(BaseModel):
    id: UUID4
    adjustment_number: str
    status: str

    class Config:
        from_attributes = True

class MaterialResponse(BaseModel):
    id: UUID4
    material_code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    base_unit: str
    active: bool = True

    class Config:
        from_attributes = True

class MaterialCreate(BaseModel):
    material_code: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    base_unit: str

class WarehouseResponse(BaseModel):
    id: UUID4
    code: str
    name: str
    location: Optional[str] = None
    type: str

    class Config:
        from_attributes = True

class WarehouseCreate(BaseModel):
    code: str
    name: str
    location: Optional[str] = None
    type: str = "CENTRAL"

class InventoryTransactionResponse(BaseModel):
    id: UUID4
    warehouse_id: UUID4
    material_id: UUID4
    project_id: Optional[UUID4] = None
    transaction_type: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
    reference_type: Optional[str] = None
    transaction_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class InventoryBalanceDetailResponse(BaseModel):
    id: UUID4
    warehouse_id: UUID4
    warehouse_name: str
    material_id: UUID4
    material_code: str
    material_name: str
    base_unit: str
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal
