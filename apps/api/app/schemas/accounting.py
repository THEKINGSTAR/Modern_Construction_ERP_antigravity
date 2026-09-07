from typing import List, Optional, Any
from uuid import UUID
from datetime import date
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from app.models.accounting import AccountType, JournalStatus

# Chart of Accounts
class ChartOfAccountsBase(BaseModel):
    name: str
    description: Optional[str] = None

class ChartOfAccountsCreate(ChartOfAccountsBase):
    pass

class ChartOfAccountsResponse(ChartOfAccountsBase):
    id: UUID

    class Config:
        from_attributes = True

# Accounts
class AccountBase(BaseModel):
    name: str
    account_code: str
    account_type: AccountType
    is_control_account: bool = False
    parent_id: Optional[UUID] = None
    chart_of_accounts_id: Optional[UUID] = None

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: UUID
    chart_name: Optional[str] = None
    parent_code: Optional[str] = None
    parent_name: Optional[str] = None
    balance: Optional[Decimal] = Decimal("0.0000")
    total_debit: Optional[Decimal] = Decimal("0.0000")
    total_credit: Optional[Decimal] = Decimal("0.0000")

    class Config:
        from_attributes = True

# Journal Lines
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
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None

    class Config:
        from_attributes = True

# Journals
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
    lines_count: Optional[int] = 0
    total_debit: Optional[Decimal] = Decimal("0.0000")
    total_credit: Optional[Decimal] = Decimal("0.0000")
    is_balanced: Optional[bool] = True

    class Config:
        from_attributes = True

# Accounting Periods
class AccountingPeriodResponse(BaseModel):
    id: UUID
    fiscal_year_id: UUID
    name: str
    start_date: date
    end_date: date
    is_closed: bool
    fiscal_year_name: Optional[str] = None

    class Config:
        from_attributes = True

class AccountingPeriodCloseRequest(BaseModel):
    is_closed: bool

# General Ledger Balance Query
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

# Summary / Dashboard
class GLSummaryResponse(BaseModel):
    total_journals: int
    posted_journals: int
    draft_journals: int
    reversed_journals: int
    total_debits: Decimal
    total_credits: Decimal
    is_ledger_balanced: bool
    total_accounts: int
    asset_accounts: int
    liability_accounts: int
    equity_accounts: int
    revenue_accounts: int
    expense_accounts: int
    total_periods: int
    open_periods: int
    closed_periods: int
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal

# Financial Statements
class FinancialStatementItem(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    account_type: str
    debit: Decimal = Decimal("0.0000")
    credit: Decimal = Decimal("0.0000")
    balance: Decimal = Decimal("0.0000")

class BalanceSheetReport(BaseModel):
    as_of_date: date
    assets: List[FinancialStatementItem]
    total_assets: Decimal
    liabilities: List[FinancialStatementItem]
    total_liabilities: Decimal
    equity: List[FinancialStatementItem]
    total_equity: Decimal
    retained_earnings: Decimal
    total_liabilities_and_equity: Decimal
    is_balanced: bool

class IncomeStatementReport(BaseModel):
    start_date: date
    end_date: date
    revenue: List[FinancialStatementItem]
    total_revenue: Decimal
    expenses: List[FinancialStatementItem]
    total_expenses: Decimal
    gross_profit: Decimal
    net_profit: Decimal
