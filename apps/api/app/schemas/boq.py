from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# --- BOQ Item ---
class BOQItemBase(BaseModel):
    item_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)
    unit: str = Field(..., max_length=50)
    quantity: Decimal = Field(..., max_digits=18, decimal_places=4)
    unit_rate: Decimal = Field(..., max_digits=18, decimal_places=4)
    cost_code_id: Optional[UUID] = None

class BOQItemCreate(BOQItemBase):
    pass

class BOQItemUpdate(BaseModel):
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)
    unit_rate: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)
    cost_code_id: Optional[UUID] = None

class BOQItemResponse(BOQItemBase):
    id: UUID
    revision_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True

# --- BOQ Revision ---
class BOQRevisionBase(BaseModel):
    status: str = "DRAFT"

class BOQRevisionCreate(BOQRevisionBase):
    pass

class BOQRevisionResponse(BOQRevisionBase):
    id: UUID
    boq_id: UUID
    version_number: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True

class BOQRevisionWithItemsResponse(BOQRevisionResponse):
    items: List[BOQItemResponse] = []
    
    class ConfigDict:
        from_attributes = True

# --- BOQ ---
class BOQBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: UUID

class BOQCreate(BOQBase):
    pass

class BOQUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)

class BOQResponse(BOQBase):
    id: UUID
    status: str
    current_revision_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True
