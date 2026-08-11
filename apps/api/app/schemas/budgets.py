from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal

# --- Budget Line ---
class BudgetLineBase(BaseModel):
    cost_code_id: UUID
    original_budget: Decimal = Field(..., max_digits=18, decimal_places=4)
    approved_changes: Decimal = Field(..., max_digits=18, decimal_places=4)

class BudgetLineCreate(BudgetLineBase):
    pass

class BudgetLineUpdate(BaseModel):
    original_budget: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)
    approved_changes: Optional[Decimal] = Field(None, max_digits=18, decimal_places=4)

class BudgetLineResponse(BudgetLineBase):
    id: UUID
    budget_id: UUID
    
    # Calculated Fields
    current_budget: Decimal
    committed_cost: Decimal
    actual_cost: Decimal
    forecast_cost: Decimal
    variance: Decimal
    
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    model_config = ConfigDict(from_attributes=True)

# --- Budget ---
class BudgetBase(BaseModel):
    name: str = Field(..., max_length=255)
    project_id: UUID

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)

class BudgetResponse(BudgetBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[UUID]
    updated_by: Optional[UUID]
    
    model_config = ConfigDict(from_attributes=True)

class BudgetWithLinesResponse(BudgetResponse):
    lines: List[BudgetLineResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
