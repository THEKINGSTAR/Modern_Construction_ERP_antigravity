from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import UUID4
from typing import Optional, List
from datetime import date
from decimal import Decimal
from app.models.commercial import ChangeOrderStatus, PaymentAppStatus

# Subcontracts
class SubcontractBase(BaseModel):
    project_id: UUID4
    supplier_id: UUID4
    subcontract_number: str = Field(..., max_length=100)
    original_value: Decimal = Field(default=Decimal("0.0"))
    currency_code: str = Field(..., max_length=3)
    retention_rate: Decimal = Field(default=Decimal("0.0"))
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SubcontractCreate(SubcontractBase):
    pass

class SubcontractResponse(SubcontractBase):
    id: UUID4
    current_value: Decimal
    
    model_config = ConfigDict(from_attributes=True)

# Client Change Orders
class ClientChangeOrderBase(BaseModel):
    contract_id: UUID4
    number: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    amount: Decimal = Field(default=Decimal("0.0"))

class ClientChangeOrderCreate(ClientChangeOrderBase):
    pass

class ClientChangeOrderResponse(ClientChangeOrderBase):
    id: UUID4
    status: ChangeOrderStatus
    approved_date: Optional[date]
    
    model_config = ConfigDict(from_attributes=True)

# Subcontract Change Orders
class SubcontractChangeOrderBase(BaseModel):
    subcontract_id: UUID4
    number: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    amount: Decimal = Field(default=Decimal("0.0"))

class SubcontractChangeOrderCreate(SubcontractChangeOrderBase):
    pass

class SubcontractChangeOrderResponse(SubcontractChangeOrderBase):
    id: UUID4
    status: ChangeOrderStatus
    approved_date: Optional[date]
    
    model_config = ConfigDict(from_attributes=True)

# Payment Applications (Base calculations)
class PaymentApplicationCalcInput(BaseModel):
    gross_work: Decimal = Field(default=Decimal("0.0"))
    previous_certified_work: Decimal = Field(default=Decimal("0.0"))
    retention_amount: Decimal = Field(default=Decimal("0.0"))
    advance_recovery_amount: Decimal = Field(default=Decimal("0.0"))
    deductions_amount: Decimal = Field(default=Decimal("0.0"))
    adjustments_amount: Decimal = Field(default=Decimal("0.0"))

class ClientPaymentApplicationBase(PaymentApplicationCalcInput):
    contract_id: UUID4
    accounting_period_id: UUID4
    number: str = Field(..., max_length=100)
    date: date

class ClientPaymentApplicationCreate(ClientPaymentApplicationBase):
    pass

class ClientPaymentApplicationResponse(ClientPaymentApplicationBase):
    id: UUID4
    net_amount_due: Decimal
    status: PaymentAppStatus
    journal_id: Optional[UUID4]
    
    model_config = ConfigDict(from_attributes=True)

class SubcontractPaymentApplicationBase(PaymentApplicationCalcInput):
    subcontract_id: UUID4
    accounting_period_id: UUID4
    number: str = Field(..., max_length=100)
    date: date

class SubcontractPaymentApplicationCreate(SubcontractPaymentApplicationBase):
    pass

class SubcontractPaymentApplicationResponse(SubcontractPaymentApplicationBase):
    id: UUID4
    net_amount_due: Decimal
    status: PaymentAppStatus
    journal_id: Optional[UUID4]
    
    model_config = ConfigDict(from_attributes=True)
