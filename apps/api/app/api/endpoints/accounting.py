import uuid
from typing import List, Optional, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant as get_tenant_id
from app.models.user import User
from app.models.accounting import (
    ChartOfAccounts, Account, AccountType,
    Journal, JournalLine, JournalStatus
)
from app.models.org_settings import FiscalYear, AccountingPeriod
from app.schemas.accounting import (
    ChartOfAccountsResponse,
    AccountCreate, AccountResponse,
    JournalCreate, JournalResponse, JournalLineResponse,
    AccountingPeriodResponse, AccountingPeriodCloseRequest,
    GLBalanceResponse, GLBalanceQuery,
    GLSummaryResponse, BalanceSheetReport, IncomeStatementReport, FinancialStatementItem
)
from app.services.accounting import AccountingEngine

router = APIRouter()

class ReverseJournalRequest(BaseModel):
    reversal_date: date
    description: str

# ----------------------------------------------------------------------
# 1. Summary / KPI Engine
# ----------------------------------------------------------------------
@router.get("/summary", response_model=GLSummaryResponse)
def get_gl_summary(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    # Journals metrics
    journals = db.query(Journal).filter(Journal.tenant_id == tenant_id).all()
    tot_j = len(journals)
    posted_j = sum(1 for j in journals if j.status == JournalStatus.POSTED)
    draft_j = sum(1 for j in journals if j.status == JournalStatus.DRAFT)
    reversed_j = sum(1 for j in journals if j.status == JournalStatus.REVERSED)

    # Debits / Credits across posted journals
    gl_lines_q = select(
        func.coalesce(func.sum(JournalLine.debit), Decimal(0)),
        func.coalesce(func.sum(JournalLine.credit), Decimal(0))
    ).join(Journal, Journal.id == JournalLine.journal_id).where(
        Journal.tenant_id == tenant_id,
        Journal.status == JournalStatus.POSTED
    )
    tot_debit, tot_credit = db.execute(gl_lines_q).one()
    is_balanced = (tot_debit == tot_credit)

    # Accounts breakdown
    accounts = db.query(Account).filter(Account.tenant_id == tenant_id).all()
    tot_acc = len(accounts)
    asset_c = sum(1 for a in accounts if a.account_type == AccountType.ASSET)
    liab_c = sum(1 for a in accounts if a.account_type == AccountType.LIABILITY)
    eq_c = sum(1 for a in accounts if a.account_type == AccountType.EQUITY)
    rev_c = sum(1 for a in accounts if a.account_type == AccountType.REVENUE)
    exp_c = sum(1 for a in accounts if a.account_type == AccountType.EXPENSE)

    # Periods
    periods = db.query(AccountingPeriod).filter(AccountingPeriod.tenant_id == tenant_id).all()
    tot_per = len(periods)
    open_per = sum(1 for p in periods if not p.is_closed)
    closed_per = sum(1 for p in periods if p.is_closed)

    # Revenue & Expenses from posted lines
    rev_q = select(
        func.coalesce(func.sum(JournalLine.credit - JournalLine.debit), Decimal(0))
    ).join(Account, Account.id == JournalLine.account_id).join(
        Journal, Journal.id == JournalLine.journal_id
    ).where(
        Journal.tenant_id == tenant_id,
        Journal.status == JournalStatus.POSTED,
        Account.account_type == AccountType.REVENUE
    )
    total_rev = db.execute(rev_q).scalar_one()

    exp_q = select(
        func.coalesce(func.sum(JournalLine.debit - JournalLine.credit), Decimal(0))
    ).join(Account, Account.id == JournalLine.account_id).join(
        Journal, Journal.id == JournalLine.journal_id
    ).where(
        Journal.tenant_id == tenant_id,
        Journal.status == JournalStatus.POSTED,
        Account.account_type == AccountType.EXPENSE
    )
    total_exp = db.execute(exp_q).scalar_one()
    net_inc = total_rev - total_exp

    return GLSummaryResponse(
        total_journals=tot_j,
        posted_journals=posted_j,
        draft_journals=draft_j,
        reversed_journals=reversed_j,
        total_debits=tot_debit,
        total_credits=tot_credit,
        is_ledger_balanced=is_balanced,
        total_accounts=tot_acc,
        asset_accounts=asset_c,
        liability_accounts=liab_c,
        equity_accounts=eq_c,
        revenue_accounts=rev_c,
        expense_accounts=exp_c,
        total_periods=tot_per,
        open_periods=open_per,
        closed_periods=closed_per,
        total_revenue=total_rev,
        total_expenses=total_exp,
        net_income=net_inc
    )

# ----------------------------------------------------------------------
# 2. Chart of Accounts & Accounts
# ----------------------------------------------------------------------
@router.get("/chart-of-accounts", response_model=List[ChartOfAccountsResponse])
def get_charts_of_accounts(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    return db.query(ChartOfAccounts).filter(ChartOfAccounts.tenant_id == tenant_id).all()

@router.get("/accounts", response_model=List[AccountResponse])
def get_accounts(
    account_type: Optional[AccountType] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    q = db.query(Account).filter(Account.tenant_id == tenant_id)
    if account_type:
        q = q.filter(Account.account_type == account_type)
    if search:
        search_filter = f"%{search}%"
        q = q.filter(
            or_(
                Account.account_code.ilike(search_filter),
                Account.name.ilike(search_filter)
            )
        )
    accounts = q.order_by(Account.account_code).all()

    # Calculate live debit, credit, balance for each account from posted lines
    balances_q = select(
        JournalLine.account_id,
        func.coalesce(func.sum(JournalLine.debit), Decimal(0)).label("tot_debit"),
        func.coalesce(func.sum(JournalLine.credit), Decimal(0)).label("tot_credit")
    ).join(Journal, Journal.id == JournalLine.journal_id).where(
        Journal.tenant_id == tenant_id,
        Journal.status == JournalStatus.POSTED
    ).group_by(JournalLine.account_id)

    bal_map = {row.account_id: (row.tot_debit, row.tot_credit) for row in db.execute(balances_q)}

    res = []
    for acc in accounts:
        d, c = bal_map.get(acc.id, (Decimal("0.0000"), Decimal("0.0000")))
        if acc.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            bal = d - c
        else:
            bal = c - d
        res.append(AccountResponse(
            id=acc.id,
            name=acc.name,
            account_code=acc.account_code,
            account_type=acc.account_type,
            is_control_account=str(acc.is_control_account).lower() == "true",
            parent_id=acc.parent_id,
            chart_of_accounts_id=acc.chart_of_accounts_id,
            chart_name=acc.chart_name,
            parent_code=acc.parent_code,
            parent_name=acc.parent_name,
            balance=bal,
            total_debit=d,
            total_credit=c
        ))
    return res

@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account_detail(
    account_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    acc = db.query(Account).filter(Account.id == account_id, Account.tenant_id == tenant_id).first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    lines_q = select(
        func.coalesce(func.sum(JournalLine.debit), Decimal(0)),
        func.coalesce(func.sum(JournalLine.credit), Decimal(0))
    ).join(Journal, Journal.id == JournalLine.journal_id).where(
        Journal.tenant_id == tenant_id,
        Journal.status == JournalStatus.POSTED,
        JournalLine.account_id == account_id
    )
    d, c = db.execute(lines_q).one()
    bal = (d - c) if acc.account_type in [AccountType.ASSET, AccountType.EXPENSE] else (c - d)

    return AccountResponse(
        id=acc.id,
        name=acc.name,
        account_code=acc.account_code,
        account_type=acc.account_type,
        is_control_account=str(acc.is_control_account).lower() == "true",
        parent_id=acc.parent_id,
        chart_of_accounts_id=acc.chart_of_accounts_id,
        chart_name=acc.chart_name,
        parent_code=acc.parent_code,
        parent_name=acc.parent_name,
        balance=bal,
        total_debit=d,
        total_credit=c
    )

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    account_in: AccountCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    existing = db.query(Account).filter(
        Account.tenant_id == tenant_id,
        Account.account_code == account_in.account_code
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account with code '{account_in.account_code}' already exists."
        )

    # Ensure chart_of_accounts_id
    coa_id = account_in.chart_of_accounts_id
    if not coa_id:
        default_coa = db.query(ChartOfAccounts).filter(ChartOfAccounts.tenant_id == tenant_id).first()
        if not default_coa:
            default_coa = ChartOfAccounts(
                id=uuid.uuid4(),
                name="Primary Construction Chart of Accounts",
                description="Corporate master chart of accounts for construction operations",
                tenant_id=tenant_id,
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.add(default_coa)
            db.flush()
        coa_id = default_coa.id

    new_acc = Account(
        id=uuid.uuid4(),
        chart_of_accounts_id=coa_id,
        parent_id=account_in.parent_id,
        account_code=account_in.account_code,
        name=account_in.name,
        account_type=account_in.account_type,
        is_control_account=str(account_in.is_control_account).lower(),
        tenant_id=tenant_id,
        created_by=current_user.id,
        updated_by=current_user.id
    )
    db.add(new_acc)
    db.commit()
    db.refresh(new_acc)

    return AccountResponse(
        id=new_acc.id,
        name=new_acc.name,
        account_code=new_acc.account_code,
        account_type=new_acc.account_type,
        is_control_account=str(new_acc.is_control_account).lower() == "true",
        parent_id=new_acc.parent_id,
        chart_of_accounts_id=new_acc.chart_of_accounts_id,
        chart_name=new_acc.chart_name,
        parent_code=new_acc.parent_code,
        parent_name=new_acc.parent_name,
        balance=Decimal("0.0000"),
        total_debit=Decimal("0.0000"),
        total_credit=Decimal("0.0000")
    )

# ----------------------------------------------------------------------
# 3. Journals & Journal Entries
# ----------------------------------------------------------------------
@router.get("/journals", response_model=List[JournalResponse])
def get_journals(
    status_filter: Optional[JournalStatus] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    q = db.query(Journal).filter(Journal.tenant_id == tenant_id)
    if status_filter:
        q = q.filter(Journal.status == status_filter)
    if start_date:
        q = q.filter(Journal.date >= start_date)
    if end_date:
        q = q.filter(Journal.date <= end_date)
    if search:
        search_filter = f"%{search}%"
        q = q.filter(
            or_(
                Journal.reference.ilike(search_filter),
                Journal.description.ilike(search_filter)
            )
        )
    journals = q.order_by(Journal.date.desc(), Journal.created_at.desc()).all()

    res = []
    for j in journals:
        lines_resp = [
            JournalLineResponse(
                id=l.id,
                account_id=l.account_id,
                debit=l.debit,
                credit=l.credit,
                project_id=l.project_id,
                cost_code_id=l.cost_code_id,
                department_id=l.department_id,
                branch_id=l.branch_id,
                business_unit_id=l.business_unit_id,
                account_code=l.account_code,
                account_name=l.account_name,
                project_name=l.project_name,
                cost_code_code=l.cost_code_code
            ) for l in j.lines
        ]
        res.append(JournalResponse(
            id=j.id,
            date=j.date,
            reference=j.reference,
            description=j.description,
            status=j.status,
            reversal_journal_id=j.reversal_journal_id,
            lines=lines_resp,
            lines_count=j.lines_count,
            total_debit=j.total_debit,
            total_credit=j.total_credit,
            is_balanced=j.is_balanced
        ))
    return res

@router.get("/journals/{journal_id}", response_model=JournalResponse)
def get_journal_detail(
    journal_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    j = db.query(Journal).filter(Journal.id == journal_id, Journal.tenant_id == tenant_id).first()
    if not j:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal not found")

    lines_resp = [
        JournalLineResponse(
            id=l.id,
            account_id=l.account_id,
            debit=l.debit,
            credit=l.credit,
            project_id=l.project_id,
            cost_code_id=l.cost_code_id,
            department_id=l.department_id,
            branch_id=l.branch_id,
            business_unit_id=l.business_unit_id,
            account_code=l.account_code,
            account_name=l.account_name,
            project_name=l.project_name,
            cost_code_code=l.cost_code_code
        ) for l in j.lines
    ]
    return JournalResponse(
        id=j.id,
        date=j.date,
        reference=j.reference,
        description=j.description,
        status=j.status,
        reversal_journal_id=j.reversal_journal_id,
        lines=lines_resp,
        lines_count=j.lines_count,
        total_debit=j.total_debit,
        total_credit=j.total_credit,
        is_balanced=j.is_balanced
    )

@router.post("/journals", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
def create_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_in: JournalCreate,
    auto_post: bool = False
) -> Any:
    if not journal_in.reference:
        year = journal_in.date.year
        seq = db.query(Journal).filter(Journal.tenant_id == tenant_id).count() + 1
        journal_in.reference = f"JRN-{year}-{seq:04d}"

    engine = AccountingEngine(db, tenant_id, current_user.id)
    journal = engine.create_journal(journal_in, auto_post=auto_post)
    db.commit()
    db.refresh(journal)

    lines_resp = [
        JournalLineResponse(
            id=l.id,
            account_id=l.account_id,
            debit=l.debit,
            credit=l.credit,
            project_id=l.project_id,
            cost_code_id=l.cost_code_id,
            department_id=l.department_id,
            branch_id=l.branch_id,
            business_unit_id=l.business_unit_id,
            account_code=l.account_code,
            account_name=l.account_name,
            project_name=l.project_name,
            cost_code_code=l.cost_code_code
        ) for l in journal.lines
    ]
    return JournalResponse(
        id=journal.id,
        date=journal.date,
        reference=journal.reference,
        description=journal.description,
        status=journal.status,
        reversal_journal_id=journal.reversal_journal_id,
        lines=lines_resp,
        lines_count=journal.lines_count,
        total_debit=journal.total_debit,
        total_credit=journal.total_credit,
        is_balanced=journal.is_balanced
    )

@router.post("/journals/{journal_id}/post", response_model=JournalResponse)
def post_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_id: UUID
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    journal = engine.post_journal(journal_id)
    db.commit()
    db.refresh(journal)

    lines_resp = [
        JournalLineResponse(
            id=l.id,
            account_id=l.account_id,
            debit=l.debit,
            credit=l.credit,
            project_id=l.project_id,
            cost_code_id=l.cost_code_id,
            department_id=l.department_id,
            branch_id=l.branch_id,
            business_unit_id=l.business_unit_id,
            account_code=l.account_code,
            account_name=l.account_name,
            project_name=l.project_name,
            cost_code_code=l.cost_code_code
        ) for l in journal.lines
    ]
    return JournalResponse(
        id=journal.id,
        date=journal.date,
        reference=journal.reference,
        description=journal.description,
        status=journal.status,
        reversal_journal_id=journal.reversal_journal_id,
        lines=lines_resp,
        lines_count=journal.lines_count,
        total_debit=journal.total_debit,
        total_credit=journal.total_credit,
        is_balanced=journal.is_balanced
    )

@router.post("/journals/{journal_id}/reverse", response_model=JournalResponse)
def reverse_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_id: UUID,
    request: ReverseJournalRequest
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    reversal = engine.reverse_journal(journal_id, request.reversal_date, request.description)
    db.commit()
    db.refresh(reversal)

    lines_resp = [
        JournalLineResponse(
            id=l.id,
            account_id=l.account_id,
            debit=l.debit,
            credit=l.credit,
            project_id=l.project_id,
            cost_code_id=l.cost_code_id,
            department_id=l.department_id,
            branch_id=l.branch_id,
            business_unit_id=l.business_unit_id,
            account_code=l.account_code,
            account_name=l.account_name,
            project_name=l.project_name,
            cost_code_code=l.cost_code_code
        ) for l in reversal.lines
    ]
    return JournalResponse(
        id=reversal.id,
        date=reversal.date,
        reference=reversal.reference,
        description=reversal.description,
        status=reversal.status,
        reversal_journal_id=reversal.reversal_journal_id,
        lines=lines_resp,
        lines_count=reversal.lines_count,
        total_debit=reversal.total_debit,
        total_credit=reversal.total_credit,
        is_balanced=reversal.is_balanced
    )

# ----------------------------------------------------------------------
# 4. Accounting Periods & Month-End Close
# ----------------------------------------------------------------------
@router.get("/periods", response_model=List[AccountingPeriodResponse])
def get_accounting_periods(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    periods = db.query(AccountingPeriod).filter(
        AccountingPeriod.tenant_id == tenant_id
    ).order_by(AccountingPeriod.start_date.desc()).all()
    return [
        AccountingPeriodResponse(
            id=p.id,
            fiscal_year_id=p.fiscal_year_id,
            name=p.name,
            start_date=p.start_date,
            end_date=p.end_date,
            is_closed=p.is_closed,
            fiscal_year_name=p.fiscal_year_name
        ) for p in periods
    ]

@router.post("/periods/{period_id}/close", response_model=AccountingPeriodResponse)
def close_accounting_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    period = db.query(AccountingPeriod).filter(
        AccountingPeriod.id == period_id,
        AccountingPeriod.tenant_id == tenant_id
    ).first()
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting period not found")
    period.is_closed = True
    db.commit()
    db.refresh(period)
    return AccountingPeriodResponse(
        id=period.id,
        fiscal_year_id=period.fiscal_year_id,
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_closed=period.is_closed,
        fiscal_year_name=period.fiscal_year_name
    )

@router.post("/periods/{period_id}/reopen", response_model=AccountingPeriodResponse)
def reopen_accounting_period(
    period_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    period = db.query(AccountingPeriod).filter(
        AccountingPeriod.id == period_id,
        AccountingPeriod.tenant_id == tenant_id
    ).first()
    if not period:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accounting period not found")
    period.is_closed = False
    db.commit()
    db.refresh(period)
    return AccountingPeriodResponse(
        id=period.id,
        fiscal_year_id=period.fiscal_year_id,
        name=period.name,
        start_date=period.start_date,
        end_date=period.end_date,
        is_closed=period.is_closed,
        fiscal_year_name=period.fiscal_year_name
    )

# ----------------------------------------------------------------------
# 5. Financial Statements: Balance Sheet & Income Statement (P&L)
# ----------------------------------------------------------------------
@router.get("/reports/balance-sheet", response_model=BalanceSheetReport)
def get_balance_sheet(
    as_of_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    target_date = as_of_date or date.today()

    # Query all accounts with posted journal lines up to target_date
    query = select(
        Account.id,
        Account.account_code,
        Account.name,
        Account.account_type,
        func.coalesce(func.sum(JournalLine.debit), Decimal(0)).label("tot_debit"),
        func.coalesce(func.sum(JournalLine.credit), Decimal(0)).label("tot_credit")
    ).join(
        JournalLine, JournalLine.account_id == Account.id, isouter=True
    ).join(
        Journal, and_(Journal.id == JournalLine.journal_id, Journal.status == JournalStatus.POSTED, Journal.date <= target_date), isouter=True
    ).where(
        Account.tenant_id == tenant_id
    ).group_by(Account.id, Account.account_code, Account.name, Account.account_type)

    assets: List[FinancialStatementItem] = []
    liabilities: List[FinancialStatementItem] = []
    equity: List[FinancialStatementItem] = []
    tot_assets = Decimal("0.0000")
    tot_liabilities = Decimal("0.0000")
    tot_equity = Decimal("0.0000")
    tot_revenue = Decimal("0.0000")
    tot_expenses = Decimal("0.0000")

    for row in db.execute(query):
        d = row.tot_debit
        c = row.tot_credit
        if row.account_type == AccountType.ASSET:
            bal = d - c
            tot_assets += bal
            if bal != 0:
                assets.append(FinancialStatementItem(
                    account_id=row.id, account_code=row.account_code,
                    account_name=row.name, account_type=row.account_type.value,
                    debit=d, credit=c, balance=bal
                ))
        elif row.account_type == AccountType.LIABILITY:
            bal = c - d
            tot_liabilities += bal
            if bal != 0:
                liabilities.append(FinancialStatementItem(
                    account_id=row.id, account_code=row.account_code,
                    account_name=row.name, account_type=row.account_type.value,
                    debit=d, credit=c, balance=bal
                ))
        elif row.account_type == AccountType.EQUITY:
            bal = c - d
            tot_equity += bal
            if bal != 0:
                equity.append(FinancialStatementItem(
                    account_id=row.id, account_code=row.account_code,
                    account_name=row.name, account_type=row.account_type.value,
                    debit=d, credit=c, balance=bal
                ))
        elif row.account_type == AccountType.REVENUE:
            tot_revenue += (c - d)
        elif row.account_type == AccountType.EXPENSE:
            tot_expenses += (d - c)

    retained_earnings = tot_revenue - tot_expenses
    total_liab_eq = tot_liabilities + tot_equity + retained_earnings
    is_bal = abs(tot_assets - total_liab_eq) < Decimal("0.01")

    return BalanceSheetReport(
        as_of_date=target_date,
        assets=assets,
        total_assets=tot_assets,
        liabilities=liabilities,
        total_liabilities=tot_liabilities,
        equity=equity,
        total_equity=tot_equity,
        retained_earnings=retained_earnings,
        total_liabilities_and_equity=total_liab_eq,
        is_balanced=is_bal
    )

@router.get("/reports/income-statement", response_model=IncomeStatementReport)
def get_income_statement(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
) -> Any:
    today = date.today()
    s_date = start_date or date(today.year, 1, 1)
    e_date = end_date or today

    query = select(
        Account.id,
        Account.account_code,
        Account.name,
        Account.account_type,
        func.coalesce(func.sum(JournalLine.debit), Decimal(0)).label("tot_debit"),
        func.coalesce(func.sum(JournalLine.credit), Decimal(0)).label("tot_credit")
    ).join(
        JournalLine, JournalLine.account_id == Account.id, isouter=True
    ).join(
        Journal, and_(
            Journal.id == JournalLine.journal_id,
            Journal.status == JournalStatus.POSTED,
            Journal.date >= s_date,
            Journal.date <= e_date
        ), isouter=True
    ).where(
        Account.tenant_id == tenant_id,
        Account.account_type.in_([AccountType.REVENUE, AccountType.EXPENSE])
    ).group_by(Account.id, Account.account_code, Account.name, Account.account_type)

    revenue_items: List[FinancialStatementItem] = []
    expense_items: List[FinancialStatementItem] = []
    tot_rev = Decimal("0.0000")
    tot_exp = Decimal("0.0000")

    for row in db.execute(query):
        d = row.tot_debit
        c = row.tot_credit
        if row.account_type == AccountType.REVENUE:
            bal = c - d
            tot_rev += bal
            if bal != 0:
                revenue_items.append(FinancialStatementItem(
                    account_id=row.id, account_code=row.account_code,
                    account_name=row.name, account_type=row.account_type.value,
                    debit=d, credit=c, balance=bal
                ))
        elif row.account_type == AccountType.EXPENSE:
            bal = d - c
            tot_exp += bal
            if bal != 0:
                expense_items.append(FinancialStatementItem(
                    account_id=row.id, account_code=row.account_code,
                    account_name=row.name, account_type=row.account_type.value,
                    debit=d, credit=c, balance=bal
                ))

    gross_profit = tot_rev
    net_profit = tot_rev - tot_exp

    return IncomeStatementReport(
        start_date=s_date,
        end_date=e_date,
        revenue=revenue_items,
        total_revenue=tot_rev,
        expenses=expense_items,
        total_expenses=tot_exp,
        gross_profit=gross_profit,
        net_profit=net_profit
    )

# Legacy / Query GL balances
@router.post("/gl/balances", response_model=List[GLBalanceResponse])
def get_gl_balances(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    query: GLBalanceQuery
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    balances = engine.get_gl_balances(
        start_date=query.start_date,
        end_date=query.end_date,
        account_id=query.account_id,
        project_id=query.project_id,
        department_id=query.department_id,
        branch_id=query.branch_id,
        business_unit_id=query.business_unit_id
    )
    return balances
