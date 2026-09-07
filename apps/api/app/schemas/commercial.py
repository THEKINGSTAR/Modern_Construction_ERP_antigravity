from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from typing import Optional, List
from datetime import date
from decimal import Decimal
from app.models.commercial import ChangeOrderStatus, PaymentAppStatus

# Subcontracts
class SubcontractBase(BaseModel):
    project_id: UUID
    supplier_id: UUID
    subcontract_number: str = Field(..., max_length=100)
    original_value: Decimal = Field(default=Decimal("0.0"))
    currency_code: str = Field(..., max_length=3)
    retention_rate: Decimal = Field(default=Decimal("0.0"))
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class SubcontractCreate(SubcontractBase):
    pass

class SubcontractResponse(SubcontractBase):
    id: UUID
    current_value: Decimal
    project_name: Optional[str] = None
    supplier_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Client Change Orders
class ClientChangeOrderBase(BaseModel):
    contract_id: UUID
    number: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    amount: Decimal = Field(default=Decimal("0.0"))

class ClientChangeOrderCreate(ClientChangeOrderBase):
    pass

class ClientChangeOrderResponse(ClientChangeOrderBase):
    id: UUID
    status: ChangeOrderStatus
    approved_date: Optional[date] = None
    contract_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Subcontract Change Orders
class SubcontractChangeOrderBase(BaseModel):
    subcontract_id: UUID
    number: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    amount: Decimal = Field(default=Decimal("0.0"))

class SubcontractChangeOrderCreate(SubcontractChangeOrderBase):
    pass

class SubcontractChangeOrderResponse(SubcontractChangeOrderBase):
    id: UUID
    status: ChangeOrderStatus
    approved_date: Optional[date] = None
    subcontract_number: Optional[str] = None
    
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
    contract_id: UUID
    accounting_period_id: UUID
    number: str = Field(..., max_length=100)
    date: date

class ClientPaymentApplicationCreate(ClientPaymentApplicationBase):
    pass

class ClientPaymentApplicationResponse(ClientPaymentApplicationBase):
    id: UUID
    net_amount_due: Decimal
    status: PaymentAppStatus
    journal_id: Optional[UUID] = None
    contract_number: Optional[str] = None
    period_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class SubcontractPaymentApplicationBase(PaymentApplicationCalcInput):
    subcontract_id: UUID
    accounting_period_id: UUID
    number: str = Field(..., max_length=100)
    date: date

class SubcontractPaymentApplicationCreate(SubcontractPaymentApplicationBase):
    pass

class SubcontractPaymentApplicationResponse(SubcontractPaymentApplicationBase):
    id: UUID
    net_amount_due: Decimal
    status: PaymentAppStatus
    journal_id: Optional[UUID] = None
    subcontract_number: Optional[str] = None
    period_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class CommercialSummaryResponse(BaseModel):
    total_prime_contract_value: Decimal
    total_subcontracts_value: Decimal
    total_client_change_orders_approved: Decimal
    total_client_change_orders_pending: Decimal
    total_subcontract_change_orders_approved: Decimal
    total_client_billed: Decimal
    total_client_retention: Decimal
    total_subcontractor_billed: Decimal
    total_subcontractor_retention: Decimal
    subcontracts_count: int
    change_orders_count: int
    payment_applications_count: int

    model_config = ConfigDict(from_attributes=True)
