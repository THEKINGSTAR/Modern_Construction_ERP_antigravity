from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, ConfigDict
from app.models.requisitions import PRStatus

class PurchaseRequisitionLineBase(BaseModel):
    cost_code_id: Optional[UUID] = None
    item_description: str
    unit: str
    quantity: Decimal

class PurchaseRequisitionLineCreate(PurchaseRequisitionLineBase):
    pass

class PurchaseRequisitionLineResponse(PurchaseRequisitionLineBase):
    id: UUID
    requisition_id: UUID
    model_config = ConfigDict(from_attributes=True)

class PurchaseRequisitionBase(BaseModel):
    pr_number: str
    project_id: UUID
    requester_id: UUID
    description: Optional[str] = None
    status: PRStatus = PRStatus.DRAFT
    required_date: Optional[date] = None

class PurchaseRequisitionCreate(PurchaseRequisitionBase):
    lines: List[PurchaseRequisitionLineCreate]

class PurchaseRequisitionResponse(PurchaseRequisitionBase):
    id: UUID
    project_name: Optional[str] = None
    requester_name: Optional[str] = None
    lines_count: Optional[int] = None
    lines: List[PurchaseRequisitionLineResponse] = []
    model_config = ConfigDict(from_attributes=True)
