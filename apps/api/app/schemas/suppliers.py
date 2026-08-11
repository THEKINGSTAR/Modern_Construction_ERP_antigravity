from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.suppliers import SupplierStatus

class SupplierContactBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None

class SupplierContactCreate(SupplierContactBase):
    pass

class SupplierContactResponse(SupplierContactBase):
    id: UUID
    supplier_id: UUID
    model_config = ConfigDict(from_attributes=True)

class SupplierBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    tax_identifier: Optional[str] = None
    address: Optional[str] = None
    status: SupplierStatus = SupplierStatus.ACTIVE

class SupplierCreate(SupplierBase):
    contacts: List[SupplierContactCreate] = []

class SupplierResponse(SupplierBase):
    id: UUID
    contacts: List[SupplierContactResponse] = []
    model_config = ConfigDict(from_attributes=True)
