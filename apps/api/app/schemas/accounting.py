from typing import List, Optional, Any
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from app.models.accounting import AccountType, JournalStatus

class AccountBase(BaseModel):
    name: str
    account_code: str
    account_type: AccountType
    is_control_account: bool = False
    parent_id: Optional[UUID] = None
    chart_of_accounts_id: UUID

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: UUID

    class Config:
        from_attributes = True

class JournalLineBase(BaseModel):
    account_id: UUID
    debit: Decimal = Field(default=Decimal('0.0000'), max_digits=18, decimal_places=4)
    credit: Decimal = Field(default=Decimal('0.0000'), max_digits=18, decimal_places=4)
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    business_unit_id: Optional[UUID] = None

class JournalLineCreate(JournalLineBase):
    pass

class JournalLineResponse(JournalLineBase):
    id: UUID

    class Config:
        from_attributes = True

class JournalBase(BaseModel):
    date: date
    reference: Optional[str] = None
    description: str

class JournalCreate(JournalBase):
    lines: List[JournalLineCreate]

    @field_validator('lines')
    @classmethod
    def validate_balancing(cls, v: List[JournalLineCreate], info: Any) -> List[JournalLineCreate]:
        total_debits = sum(line.debit for line in v)
        total_credits = sum(line.credit for line in v)
        if total_debits != total_credits:
            raise ValueError(f"Journal must balance. Debits: {total_debits}, Credits: {total_credits}")
        return v

class JournalResponse(JournalBase):
    id: UUID
    status: JournalStatus
    reversal_journal_id: Optional[UUID] = None
    lines: List[JournalLineResponse]

    class Config:
        from_attributes = True

class GLBalanceQuery(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    account_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    business_unit_id: Optional[UUID] = None

class GLBalanceResponse(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    total_debit: Decimal
    total_credit: Decimal
    balance: Decimal
