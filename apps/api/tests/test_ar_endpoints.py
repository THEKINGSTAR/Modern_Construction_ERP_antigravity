import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session

from app.models.clients import Client
from app.models.projects import Project
from app.models.contracts import Contract, ContractType
from app.models.commercial import ClientPaymentApplication, PaymentAppStatus
from app.models.bank import BankAccount
from app.models.accounting import Account, AccountType, ChartOfAccounts, Journal, JournalStatus
from app.models.org_settings import AccountingPeriod, FiscalYear
from app.models.ap_ar import (
    ARInvoice,
    ARInvoiceLine,
    Payment,
    PaymentAllocation,
    InvoiceStatus,
    InvoiceType,
    PaymentType,
    PaymentStatus
)


@pytest.fixture
def ar_setup(db_session: Session, test_user):
    tenant_id = test_user.tenant_id

    # 1. Chart of Accounts
    coa = ChartOfAccounts(
        id=uuid.uuid4(),
        name="AR Test COA",
        tenant_id=tenant_id
    )
    db_session.add(coa)
    db_session.flush()

    # 2. Fiscal Year and open Accounting Period
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
        name="Period 2026-08 (August)",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 31),
        is_closed=False,
        tenant_id=tenant_id
    )
    db_session.add(period)
    db_session.flush()

    # 3. Accounts
    cash_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=tenant_id, account_code="1010", name="Cash & Bank", account_type=AccountType.ASSET, is_control_account="true")
    ar_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=tenant_id, account_code="1200", name="Trade AR", account_type=AccountType.ASSET, is_control_account="true")
    ret_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=tenant_id, account_code="1210", name="Retainage Receivable", account_type=AccountType.ASSET, is_control_account="false")
    rev_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=tenant_id, account_code="4010", name="Contract Revenue", account_type=AccountType.REVENUE, is_control_account="false")
    tax_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=tenant_id, account_code="2040", name="Tax Payable", account_type=AccountType.LIABILITY, is_control_account="false")
    db_session.add_all([cash_acc, ar_acc, ret_acc, rev_acc, tax_acc])
    db_session.flush()

    # 4. Bank Account
    bank = BankAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Main Operations",
        bank_name="Test Bank",
        account_number="ACC-123456",
        currency="USD",
        gl_account_id=cash_acc.id,
        is_active=True
    )
    db_session.add(bank)
    db_session.flush()

    # 5. Client
    client_obj = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="OmniCorp Real Estate",
        status="ACTIVE"
    )
    db_session.add(client_obj)
    db_session.flush()

    # 6. Project & Contract
    project = db_session.query(Project).filter(Project.tenant_id == tenant_id).first()
    if not project:
        project = Project(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            project_number=f"PRJ-AR-{uuid.uuid4().hex[:4]}",
            name="Omni Tower Construction",
            status="ACTIVE"
        )
        db_session.add(project)
        db_session.flush()

    ct_type = db_session.query(ContractType).filter(ContractType.tenant_id == tenant_id).first()
    if not ct_type:
        ct_type = ContractType(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="Lump Sum Turnkey",
            is_active=True
        )
        db_session.add(ct_type)
        db_session.flush()

    contract = Contract(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        project_id=project.id,
        client_id=client_obj.id,
        contract_type_id=ct_type.id,
        contract_number=f"CTR-AR-{uuid.uuid4().hex[:4]}",
        original_value=Decimal("5000000.00"),
        current_value=Decimal("5000000.00"),
        currency_code="USD"
    )
    db_session.add(contract)
    db_session.flush()

    # 7. Client Payment Application (IPC)
    pay_app = ClientPaymentApplication(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        contract_id=contract.id,
        accounting_period_id=period.id,
        number=f"IPC-TEST-{uuid.uuid4().hex[:4]}",
        date=date(2026, 8, 15),
        gross_work=Decimal("500000.00"),
        previous_certified_work=Decimal("0.00"),
        retention_amount=Decimal("50000.00"),
        advance_recovery_amount=Decimal("0.00"),
        deductions_amount=Decimal("0.00"),
        adjustments_amount=Decimal("0.00"),
        net_amount_due=Decimal("450000.00"),
        status=PaymentAppStatus.APPROVED
    )
    db_session.add(pay_app)
    db_session.commit()

    return {
        "client": client_obj,
        "contract": contract,
        "pay_app": pay_app,
        "bank": bank,
        "cash_acc": cash_acc,
        "ar_acc": ar_acc,
        "ret_acc": ret_acc,
        "rev_acc": rev_acc
    }


def test_ar_summary(client, auth_headers, ar_setup):
    response = client.get("/api/v1/ar/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_invoiced" in data
    assert "total_receivables" in data
    assert "total_received" in data
    assert "total_retention_held" in data
    assert "current_receivables" in data


def test_ar_invoice_lifecycle(client, auth_headers, ar_setup):
    client_id = str(ar_setup["client"].id)

    # 1. Create Invoice
    payload = {
        "number": f"INV-TEST-{uuid.uuid4().hex[:4]}",
        "client_id": client_id,
        "date": "2026-08-15",
        "due_date": "2026-09-15",
        "invoice_type": "STANDARD",
        "description": "Direct Commercial Billing",
        "retention_amount": 10000.0,
        "lines": [
            {
                "description": "Foundation Pouring",
                "quantity": 100.0,
                "unit_price": 1000.0,
                "tax_rate": 0.0
            }
        ]
    }
    create_resp = client.post("/api/v1/ar/invoices", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    inv = create_resp.json()
    inv_id = inv["id"]
    assert inv["status"] == "DRAFT"
    assert float(inv["subtotal"]) == 100000.0
    assert float(inv["retention_amount"]) == 10000.0
    assert float(inv["total_amount"]) == 90000.0  # subtotal - retention

    # 2. Approve Invoice
    approve_resp = client.post(f"/api/v1/ar/invoices/{inv_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

    # 3. Get Invoice Details
    get_resp = client.get(f"/api/v1/ar/invoices/{inv_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == inv_id


def test_ar_invoice_posting_balanced(client, auth_headers, ar_setup, db_session):
    client_id = str(ar_setup["client"].id)

    payload = {
        "number": f"INV-TEST-POST-{uuid.uuid4().hex[:4]}",
        "client_id": client_id,
        "date": "2026-08-15",
        "due_date": "2026-09-15",
        "retention_amount": 20000.0,
        "lines": [
            {
                "description": "Structural Steel Framing",
                "quantity": 2.0,
                "unit_price": 100000.0
            }
        ]
    }
    create_resp = client.post("/api/v1/ar/invoices", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    inv_id = create_resp.json()["id"]

    # Post invoice to GL
    post_resp = client.post(f"/api/v1/ar/invoices/{inv_id}/post", headers=auth_headers)
    assert post_resp.status_code == 200
    posted_inv = post_resp.json()
    assert posted_inv["status"] == "POSTED"
    assert posted_inv["journal_id"] is not None

    # Check journal in DB
    journal = db_session.query(Journal).filter(Journal.id == uuid.UUID(posted_inv["journal_id"])).first()
    assert journal is not None
    assert journal.status == JournalStatus.POSTED
    total_debits = sum(l.debit for l in journal.lines)
    total_credits = sum(l.credit for l in journal.lines)
    assert total_debits == total_credits == Decimal("200000.00")


def test_ar_invoice_from_payment_application(client, auth_headers, ar_setup):
    pay_app_id = str(ar_setup["pay_app"].id)

    resp = client.post(f"/api/v1/ar/invoices/from-payment-application/{pay_app_id}", headers=auth_headers)
    assert resp.status_code == 201
    inv = resp.json()
    assert "INV-AR-IPC-TEST" in inv["number"]
    assert float(inv["subtotal"]) == 500000.0
    assert float(inv["retention_amount"]) == 50000.0
    assert float(inv["total_amount"]) == 450000.0
    assert inv["payment_application_id"] == pay_app_id


def test_ar_customer_receipt_and_settlement(client, auth_headers, ar_setup):
    client_id = str(ar_setup["client"].id)
    bank_id = str(ar_setup["bank"].id)

    # 1. Create and post an invoice for $50,000 net
    payload = {
        "number": f"INV-TEST-REC-{uuid.uuid4().hex[:4]}",
        "client_id": client_id,
        "date": "2026-08-15",
        "due_date": "2026-09-15",
        "retention_amount": 0.0,
        "lines": [
            {
                "description": "Architectural Cladding",
                "quantity": 1.0,
                "unit_price": 50000.0
            }
        ]
    }
    inv_resp = client.post("/api/v1/ar/invoices", json=payload, headers=auth_headers)
    inv_id = inv_resp.json()["id"]
    client.post(f"/api/v1/ar/invoices/{inv_id}/post", headers=auth_headers)

    # 2. Create customer collection receipt for $50,000 (Full Settlement)
    receipt_payload = {
        "reference": f"REC-TEST-FULL-{uuid.uuid4().hex[:4]}",
        "payment_type": "AR_RECEIPT",
        "date": "2026-08-20",
        "amount": 50000.0,
        "currency": "USD",
        "client_id": client_id,
        "bank_account_id": bank_id,
        "allocations": [
            {
                "ar_invoice_id": inv_id,
                "amount": 50000.0
            }
        ]
    }
    rec_resp = client.post("/api/v1/ar/receipts", json=receipt_payload, headers=auth_headers)
    assert rec_resp.status_code == 201
    receipt = rec_resp.json()
    assert receipt["status"] == "POSTED"
    assert receipt["journal_id"] is not None

    # 3. Check invoice status transitioned to PAID
    inv_detail = client.get(f"/api/v1/ar/invoices/{inv_id}", headers=auth_headers).json()
    assert inv_detail["status"] == "PAID"
    assert float(inv_detail["outstanding_amount"]) == 0.0
    assert float(inv_detail["paid_amount"]) == 50000.0
