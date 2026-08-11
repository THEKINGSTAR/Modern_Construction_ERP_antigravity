from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.cost_codes import CostCategory

class CostCodeBase(BaseModel):
    parent_id: Optional[UUID] = None
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    category: Optional[CostCategory] = None
    is_active: bool = True

class CostCodeCreate(CostCodeBase):
    pass

class CostCodeUpdate(BaseModel):
    parent_id: Optional[UUID] = None
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[CostCategory] = None
    is_active: Optional[bool] = None

class CostCodeResponse(CostCodeBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CostCodeTreeResponse(CostCodeResponse):
    children: List['CostCodeTreeResponse'] = []

    class Config:
        from_attributes = True
