from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

class WBSNodeBase(BaseModel):
    project_id: UUID
    parent_id: Optional[UUID] = None
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: bool = True

class WBSNodeCreate(WBSNodeBase):
    pass

class WBSNodeUpdate(BaseModel):
    parent_id: Optional[UUID] = None
    code: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None

class WBSNodeResponse(WBSNodeBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WBSNodeTreeResponse(WBSNodeResponse):
    children: List['WBSNodeTreeResponse'] = []

    class Config:
        from_attributes = True
