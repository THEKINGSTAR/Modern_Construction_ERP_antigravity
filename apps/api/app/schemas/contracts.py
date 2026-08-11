from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.contracts import ContractStatus

# --- Contract Type Schemas ---

class ContractTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

class ContractTypeCreate(ContractTypeBase):
    pass

class ContractTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class ContractTypeResponse(ContractTypeBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Contract Schemas ---

class ContractBase(BaseModel):
    project_id: UUID
    client_id: Optional[UUID] = None
    contract_number: str = Field(..., max_length=100)
    contract_type_id: UUID
    original_value: float = Field(0.0)
    current_value: float = Field(0.0)
    currency_code: str = Field(..., max_length=3)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    retention_rate: float = Field(0.0)
    payment_terms: Optional[str] = Field(None, max_length=255)
    status: ContractStatus = ContractStatus.DRAFT

class ContractCreate(ContractBase):
    pass

class ContractUpdate(BaseModel):
    project_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    contract_number: Optional[str] = Field(None, max_length=100)
    contract_type_id: Optional[UUID] = None
    original_value: Optional[float] = None
    current_value: Optional[float] = None
    currency_code: Optional[str] = Field(None, max_length=3)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    retention_rate: Optional[float] = None
    payment_terms: Optional[str] = Field(None, max_length=255)
    status: Optional[ContractStatus] = None

class ContractResponse(ContractBase):
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
