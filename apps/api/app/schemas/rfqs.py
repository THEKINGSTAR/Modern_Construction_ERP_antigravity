from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date
from pydantic import BaseModel, ConfigDict
from app.models.rfqs import RFQStatus

class RFQLineBase(BaseModel):
    pr_line_id: Optional[UUID] = None
    item_description: str
    unit: str
    quantity: Decimal

class RFQLineCreate(RFQLineBase):
    pass

class RFQLineResponse(RFQLineBase):
    id: UUID
    rfq_id: UUID
    model_config = ConfigDict(from_attributes=True)

class RFQBase(BaseModel):
    rfq_number: str
    project_id: UUID
    requisition_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    status: RFQStatus = RFQStatus.DRAFT
    due_date: Optional[date] = None

class RFQCreate(RFQBase):
    lines: List[RFQLineCreate]

class RFQResponse(RFQBase):
    id: UUID
    lines: List[RFQLineResponse] = []
    model_config = ConfigDict(from_attributes=True)
