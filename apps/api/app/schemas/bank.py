from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from uuid import UUID
from decimal import Decimal
from app.models.bank import BankTransactionType, BankStatementStatus

# Bank Account
class BankAccountBase(BaseModel):
    name: str = Field(..., max_length=100)
    account_number: str = Field(..., max_length=50)
    bank_name: str = Field(..., max_length=100)
    currency: str = Field(default="USD", max_length=3)
    gl_account_id: UUID
    is_active: bool = True

class BankAccountCreate(BankAccountBase):
    pass

class BankAccountResponse(BankAccountBase):
    id: UUID
    
    class Config:
        from_attributes = True

# Bank Transaction
class BankTransactionBase(BaseModel):
    date: date
    transaction_type: BankTransactionType
    amount: Decimal = Field(..., max_digits=18, decimal_places=4)
    reference: Optional[str] = None
    description: Optional[str] = None

class BankTransactionCreate(BankTransactionBase):
    bank_account_id: UUID

class BankTransactionResponse(BankTransactionBase):
    id: UUID
    bank_account_id: UUID
    reconciled: bool
    payment_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

# Bank Statement Line
class BankStatementLineBase(BaseModel):
    date: date
    description: str
    amount: Decimal = Field(..., max_digits=18, decimal_places=4)

class BankStatementLineCreate(BankStatementLineBase):
    pass

class BankStatementLineResponse(BankStatementLineBase):
    id: UUID
    statement_id: UUID
    matched: bool
    bank_transaction_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True

# Bank Statement
class BankStatementBase(BaseModel):
    statement_date: date
    opening_balance: Decimal = Field(..., max_digits=18, decimal_places=4)
    closing_balance: Decimal = Field(..., max_digits=18, decimal_places=4)

class BankStatementCreate(BankStatementBase):
    bank_account_id: UUID
    lines: List[BankStatementLineCreate]

class BankStatementResponse(BankStatementBase):
    id: UUID
    bank_account_id: UUID
    status: BankStatementStatus
    lines: List[BankStatementLineResponse]
    
    class Config:
        from_attributes = True

# Reconciliation Match
class ReconciliationMatchRequest(BaseModel):
    statement_line_id: UUID
    bank_transaction_id: UUID
