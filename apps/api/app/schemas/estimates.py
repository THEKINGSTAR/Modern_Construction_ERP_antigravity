from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# --- Estimate Item ---
class EstimateItemBase(BaseModel):
    item_code: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)
    unit: str = Field(..., max_length=50)
    quantity: Decimal = Field(..., max_digits=18, decimal_places=4)
    unit_rate: Decimal = Field(..., max_digits=18, decimal_places=4)
    cost_code_id: Optional[UUID] = None

class EstimateItemCreate(EstimateItemBase):
    pass

class EstimateItemUpdate(BaseModel):
    item_code: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    unit: Optional[str] = Field(None, max_length=50)
    quantity: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)
    unit_rate: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)
    cost_code_id: Optional[UUID] = None

class EstimateItemResponse(EstimateItemBase):
    id: UUID
    revision_id: UUID
    amount: Decimal
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True

# --- Estimate Revision ---
class EstimateRevisionBase(BaseModel):
    status: str = "DRAFT"

class EstimateRevisionCreate(EstimateRevisionBase):
    pass

class EstimateRevisionResponse(EstimateRevisionBase):
    id: UUID
    estimate_id: UUID
    version_number: int
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True

class EstimateRevisionWithItemsResponse(EstimateRevisionResponse):
    items: List[EstimateItemResponse] = []
    
    class ConfigDict:
        from_attributes = True

# --- Estimate ---
class EstimateBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: UUID

class EstimateCreate(EstimateBase):
    pass

class EstimateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)

class EstimateResponse(EstimateBase):
    id: UUID
    status: str
    current_revision_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    class ConfigDict:
        from_attributes = True
