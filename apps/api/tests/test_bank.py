import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from app.models.bank import BankTransactionType, BankStatementStatus

def test_bank_reconciliation(client, test_user, db_session, auth_headers):
    # Setup account
    from app.models.accounting import Account, AccountType, ChartOfAccounts
    coa = ChartOfAccounts(tenant_id=test_user.tenant_id, name="Test COA")
    db_session.add(coa)
    db_session.flush()

    cash_acc = Account(tenant_id=test_user.tenant_id, name="Cash", account_type=AccountType.ASSET, chart_of_accounts_id=coa.id, account_code="1000")
    db_session.add(cash_acc)
    db_session.commit()

    # Use auth_headers instead of manual headers

    # 1. Create Bank Account
    bank_data = {
        "name": "Checking",
        "account_number": "CHK123",
        "bank_name": "Chase",
        "currency": "USD",
        "gl_account_id": str(cash_acc.id)
    }
    resp = client.post("/api/v1/bank/accounts", json=bank_data, headers=auth_headers)
    assert resp.status_code == 201
    bank_acc = resp.json()

    # 2. Record Transaction
    txn_data = {
        "bank_account_id": bank_acc["id"],
        "date": "2026-08-15",
        "transaction_type": "WITHDRAWAL",
        "amount": 100.0,
        "reference": "REF1"
    }
    resp = client.post("/api/v1/bank/transactions", json=txn_data, headers=auth_headers)
    assert resp.status_code == 201
    txn = resp.json()

    # 3. Import Statement
    stmt_data = {
        "bank_account_id": bank_acc["id"],
        "statement_date": "2026-08-31",
        "opening_balance": 1000.0,
        "closing_balance": 900.0,
        "lines": [
            {
                "date": "2026-08-16",
                "description": "ACH Withdrawal",
                "amount": 100.0
            }
        ]
    }
    resp = client.post("/api/v1/bank/statements", json=stmt_data, headers=auth_headers)
    assert resp.status_code == 201
    stmt = resp.json()
    stmt_line_id = stmt["lines"][0]["id"]

    # 4. Match Transaction
    match_data = {
        "statement_line_id": stmt_line_id,
        "bank_transaction_id": txn["id"]
    }
    resp = client.post("/api/v1/bank/reconciliation/match", json=match_data, headers=auth_headers)
    assert resp.status_code == 200
    matched_line = resp.json()
    assert matched_line["matched"] is True

    # 5. Reconcile Statement
    resp = client.post(f"/api/v1/bank/statements/{stmt['id']}/reconcile", headers=auth_headers)
    assert resp.status_code == 200
    rec_stmt = resp.json()
    assert rec_stmt["status"] == "RECONCILED"

    # Verify transaction is reconciled
    from app.models.bank import BankTransaction
    import uuid
    db_session.expire_all()
    db_txn = db_session.query(BankTransaction).get(uuid.UUID(txn["id"]))
    assert db_txn.reconciled is True
