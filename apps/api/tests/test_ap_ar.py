import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta
from app.models.ap_ar import InvoiceStatus, PaymentStatus, InvoiceType, PaymentType
from app.models.accounting import AccountType

def test_ap_lifecycle(client, test_user, db_session, auth_headers):
    # Create test accounts
    from app.models.accounting import Account
    # Create Chart of Accounts
    from app.models.accounting import ChartOfAccounts
    coa = ChartOfAccounts(tenant_id=test_user.tenant_id, name="Test COA")
    db_session.add(coa)
    db_session.flush()

    ap_acc = Account(tenant_id=test_user.tenant_id, name="Accounts Payable", account_type=AccountType.LIABILITY, chart_of_accounts_id=coa.id, account_code="2000")
    exp_acc = Account(tenant_id=test_user.tenant_id, name="General Expense", account_type=AccountType.EXPENSE, chart_of_accounts_id=coa.id, account_code="5000")
    cash_acc = Account(tenant_id=test_user.tenant_id, name="Cash", account_type=AccountType.ASSET, chart_of_accounts_id=coa.id, account_code="1000")
    db_session.add_all([ap_acc, exp_acc, cash_acc])

    # Setup fiscal period
    from app.models.org_settings import FiscalYear, AccountingPeriod
    fy = FiscalYear(tenant_id=test_user.tenant_id, name="2026", start_date=date(2026,1,1), end_date=date(2026,12,31))
    db_session.add(fy)
    db_session.flush()
    ap = AccountingPeriod(tenant_id=test_user.tenant_id, fiscal_year_id=fy.id, name="Aug 2026", start_date=date(2026,8,1), end_date=date(2026,8,31), is_closed=False)
    db_session.add(ap)
    
    # Create Supplier
    from app.models.suppliers import Supplier
    supplier = Supplier(tenant_id=test_user.tenant_id, name="Test Supplier")
    db_session.add(supplier)
    
    # Create Bank Account
    from app.models.bank import BankAccount
    bank_acc = BankAccount(tenant_id=test_user.tenant_id, name="Operating", account_number="123", bank_name="Bank", gl_account_id=cash_acc.id)
    db_session.add(bank_acc)
    db_session.commit()

    # Use auth_headers instead of manual headers

    # 1. Create AP Invoice
    invoice_data = {
        "number": "INV-100",
        "supplier_id": str(supplier.id),
        "date": "2026-08-15",
        "due_date": "2026-08-30",
        "invoice_type": "STANDARD",
        "currency": "USD",
        "lines": [
            {
                "description": "Services",
                "quantity": 2.0,
                "unit_price": 500.0
            }
        ]
    }
    resp = client.post("/api/v1/ap/invoices", json=invoice_data, headers=auth_headers)
    assert resp.status_code == 201
    inv = resp.json()
    assert inv["total_amount"] == "1000.0000"
    assert inv["status"] == "DRAFT"

    # 2. Post AP Invoice -> GL
    resp = client.post(f"/api/v1/ap/invoices/{inv['id']}/post", headers=auth_headers)
    assert resp.status_code == 200
    posted_inv = resp.json()
    assert posted_inv["status"] == "POSTED"
    assert posted_inv["journal_id"] is not None

    # 3. Create Partial Payment -> GL
    payment_data = {
        "reference": "CHK-001",
        "payment_type": "AP_PAYMENT",
        "date": "2026-08-16",
        "amount": 400.0,
        "supplier_id": str(supplier.id),
        "bank_account_id": str(bank_acc.id),
        "allocations": [
            {
                "ap_invoice_id": inv["id"],
                "amount": 400.0
            }
        ]
    }
    resp = client.post("/api/v1/ap/payments", json=payment_data, headers=auth_headers)
    assert resp.status_code == 201
    payment = resp.json()
    assert payment["status"] == "POSTED"

    # 4. Verify Invoice outstanding balance
    db_session.expire_all()
    from app.models.ap_ar import APInvoice
    import uuid
    db_inv = db_session.query(APInvoice).get(uuid.UUID(inv["id"]))
    assert db_inv.status == InvoiceStatus.PARTIAL
