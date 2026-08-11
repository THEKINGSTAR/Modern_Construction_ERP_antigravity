from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from uuid import UUID

class ClientContactBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    is_primary: bool = False

class ClientContactCreate(ClientContactBase):
    pass

class ClientContactUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None

class ClientContactResponse(ClientContactBase):
    id: UUID
    client_id: UUID

    model_config = ConfigDict(from_attributes=True)

class ClientBase(BaseModel):
    name: str = Field(..., max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    contact_information: Optional[str] = None
    billing_address: Optional[str] = None
    tax_identifier: Optional[str] = Field(None, max_length=100)
    status: str = Field("ACTIVE", max_length=50)

class ClientCreate(ClientBase):
    contacts: Optional[List[ClientContactCreate]] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    contact_information: Optional[str] = None
    billing_address: Optional[str] = None
    tax_identifier: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, max_length=50)

class ClientResponse(ClientBase):
    id: UUID
    
    model_config = ConfigDict(from_attributes=True)

class ClientDetailResponse(ClientResponse):
    contacts: List[ClientContactResponse] = []
