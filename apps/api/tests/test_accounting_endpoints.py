import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.accounting import Account, AccountType, ChartOfAccounts, Journal, JournalStatus
from app.models.org_settings import FiscalYear, AccountingPeriod

@pytest.fixture
def accounting_setup(db_session: Session, test_tenant, test_user):
    tenant_id = test_tenant.id

    # 1. Chart of Accounts
    coa = ChartOfAccounts(
        id=uuid.uuid4(),
        name="Test COA",
        tenant_id=tenant_id
    )
    db_session.add(coa)
    db_session.flush()

    # 2. Fiscal Year & Open Accounting Period
    fy = FiscalYear(
        id=uuid.uuid4(),
        name="FY-2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_closed=False,
        tenant_id=tenant_id
    )
    db_session.add(fy)
    db_session.flush()

    period = AccountingPeriod(
        id=uuid.uuid4(),
        fiscal_year_id=fy.id,
        name="Period 2026-09 (September)",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        is_closed=False,
        tenant_id=tenant_id
    )
    db_session.add(period)
    db_session.flush()

    # 3. Base Accounts
    acc_cash = Account(
        id=uuid.uuid4(),
        chart_of_accounts_id=coa.id,
        account_code="1010",
        name="Cash & Operating Bank",
        account_type=AccountType.ASSET,
        is_control_account="true",
        tenant_id=tenant_id
    )
    acc_ap = Account(
        id=uuid.uuid4(),
        chart_of_accounts_id=coa.id,
        account_code="2010",
        name="Accounts Payable - Trade",
        account_type=AccountType.LIABILITY,
        is_control_account="true",
        tenant_id=tenant_id
    )
    acc_exp = Account(
        id=uuid.uuid4(),
        chart_of_accounts_id=coa.id,
        account_code="5010",
        name="Direct Materials Expense",
        account_type=AccountType.EXPENSE,
        is_control_account="false",
        tenant_id=tenant_id
    )
    db_session.add_all([acc_cash, acc_ap, acc_exp])
    db_session.commit()

    return {
        "coa": coa,
        "fy": fy,
        "period": period,
        "acc_cash": acc_cash,
        "acc_ap": acc_ap,
        "acc_exp": acc_exp
    }

def test_gl_summary(client, auth_headers, accounting_setup):
    response = client.get("/api/v1/accounting/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_journals" in data
    assert "total_debits" in data
    assert "total_credits" in data
    assert "is_ledger_balanced" in data
    assert "total_accounts" in data
    assert data["is_ledger_balanced"] is True

def test_accounts_lifecycle(client, auth_headers, accounting_setup):
    # 1. List accounts
    response = client.get("/api/v1/accounting/accounts", headers=auth_headers)
    assert response.status_code == 200
    accounts = response.json()
    assert len(accounts) >= 3

    # 2. Create new test account
    rand_code = f"99{uuid.uuid4().hex[:4].upper()}"
    new_acc_payload = {
        "account_code": rand_code,
        "name": f"Test Contingency Reserve {rand_code}",
        "account_type": "EXPENSE",
        "is_control_account": False
    }
    create_res = client.post("/api/v1/accounting/accounts", json=new_acc_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["account_code"] == rand_code
    assert created["name"] == f"Test Contingency Reserve {rand_code}"
    acc_id = created["id"]

    # 3. Retrieve account detail
    detail_res = client.get(f"/api/v1/accounting/accounts/{acc_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == acc_id
    assert float(detail["balance"]) == 0.0

def test_journal_voucher_workflow(client, auth_headers, accounting_setup):
    acc_cash = accounting_setup["acc_cash"]
    acc_ap = accounting_setup["acc_ap"]

    rand_ref = f"JRN-TEST-{uuid.uuid4().hex[:4].upper()}"
    entry_date = "2026-09-15"

    # 1. Attempt unbalanced journal -> must fail with 422
    unbalanced_payload = {
        "date": entry_date,
        "reference": rand_ref,
        "description": "Unbalanced Journal Test",
        "lines": [
            {"account_id": str(acc_cash.id), "debit": 5000.0, "credit": 0.0},
            {"account_id": str(acc_ap.id), "debit": 0.0, "credit": 4000.0}
        ]
    }
    bad_res = client.post("/api/v1/accounting/journals", json=unbalanced_payload, headers=auth_headers)
    assert bad_res.status_code == 422

    # 2. Create balanced journal
    balanced_payload = {
        "date": entry_date,
        "reference": rand_ref,
        "description": "Balanced Test Journal Voucher",
        "lines": [
            {"account_id": str(acc_cash.id), "debit": 5000.0, "credit": 0.0},
            {"account_id": str(acc_ap.id), "debit": 0.0, "credit": 5000.0}
        ]
    }
    good_res = client.post("/api/v1/accounting/journals", json=balanced_payload, headers=auth_headers)
    assert good_res.status_code == 201
    journal = good_res.json()
    assert journal["reference"] == rand_ref
    assert journal["status"] == "DRAFT"
    assert float(journal["total_debit"]) == 5000.0
    assert float(journal["total_credit"]) == 5000.0
    assert journal["is_balanced"] is True
    journal_id = journal["id"]

    # 3. Post the journal
    post_res = client.post(f"/api/v1/accounting/journals/{journal_id}/post", headers=auth_headers)
    assert post_res.status_code == 200
    posted = post_res.json()
    assert posted["status"] == "POSTED"

def test_financial_periods(client, auth_headers, accounting_setup):
    # 1. List periods
    res = client.get("/api/v1/accounting/periods", headers=auth_headers)
    assert res.status_code == 200
    periods = res.json()
    assert len(periods) >= 1
    period_id = periods[0]["id"]

    # 2. Close period
    close_res = client.post(f"/api/v1/accounting/periods/{period_id}/close", headers=auth_headers)
    assert close_res.status_code == 200
    assert close_res.json()["is_closed"] is True

    # 3. Reopen period
    reopen_res = client.post(f"/api/v1/accounting/periods/{period_id}/reopen", headers=auth_headers)
    assert reopen_res.status_code == 200
    assert reopen_res.json()["is_closed"] is False

def test_financial_statements(client, auth_headers, accounting_setup):
    # 1. Balance Sheet
    bs_res = client.get("/api/v1/accounting/reports/balance-sheet", headers=auth_headers)
    assert bs_res.status_code == 200
    bs = bs_res.json()
    assert "total_assets" in bs
    assert "total_liabilities" in bs
    assert "total_equity" in bs
    assert "is_balanced" in bs
    assert bs["is_balanced"] is True

    # 2. Income Statement
    is_res = client.get("/api/v1/accounting/reports/income-statement", headers=auth_headers)
    assert is_res.status_code == 200
    inc = is_res.json()
    assert "total_revenue" in inc
    assert "total_expenses" in inc
    assert "net_profit" in inc
