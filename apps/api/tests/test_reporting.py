import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.projects import Project, ProjectStatus
from app.models.contracts import Contract, ContractType, ContractStatus
from app.models.commercial import ClientPaymentApplication, PaymentAppStatus
from app.models.ap_ar import APInvoice, ARInvoice, APInvoiceLine, ARInvoiceLine, Payment, PaymentAllocation, PaymentType, PaymentStatus, InvoiceStatus
from app.models.accounting import Journal, JournalLine, Account, AccountType, ChartOfAccounts, JournalStatus
from app.models.suppliers import Supplier
from app.models.clients import Client

def test_project_dashboard_and_reporting(client: TestClient, db_session: Session, auth_headers, test_tenant):
    tenant_id = test_tenant.id

    # 1. Setup Base Entities
    project = Project(name="Report Project", project_number="REP-01", status=ProjectStatus.ACTIVE, tenant_id=tenant_id)
    client_ent = Client(name="Report Client", tenant_id=tenant_id)
    supplier_ent = Supplier(name="Report Supplier", tenant_id=tenant_id)
    db_session.add_all([project, client_ent, supplier_ent])
    db_session.flush()

    # 2. Contract
    ctype = ContractType(name="Standard", tenant_id=tenant_id)
    db_session.add(ctype)
    db_session.flush()
    contract = Contract(
        project_id=project.id,
        client_id=client_ent.id,
        contract_number="CTR-REP-01",
        contract_type_id=ctype.id,
        original_value=Decimal("100000.00"),
        current_value=Decimal("100000.00"),
        currency_code="USD",
        status=ContractStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(contract)
    db_session.flush()

    # 3. AP Invoice & Payment
    ap_inv = APInvoice(
        number="AP-REP-01",
        supplier_id=supplier_ent.id,
        date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.POSTED,
        total_amount=Decimal("1500.00"),
        tenant_id=tenant_id
    )
    db_session.add(ap_inv)
    db_session.flush()
    ap_line = APInvoiceLine(
        invoice_id=ap_inv.id,
        project_id=project.id,
        description="Subcontractor work",
        unit_price=Decimal("1500.00"),
        line_total=Decimal("1500.00"),
        tenant_id=tenant_id
    )
    db_session.add(ap_line)
    db_session.flush()
    
    # 4. AR Invoice & Payment
    ar_inv = ARInvoice(
        number="AR-REP-01",
        client_id=client_ent.id,
        date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.POSTED,
        total_amount=Decimal("10000.00"),
        tenant_id=tenant_id
    )
    db_session.add(ar_inv)
    db_session.flush()
    ar_line = ARInvoiceLine(
        invoice_id=ar_inv.id,
        project_id=project.id,
        description="Billing Milestone 1",
        unit_price=Decimal("10000.00"),
        line_total=Decimal("10000.00"),
        tenant_id=tenant_id
    )
    db_session.add(ar_line)
    db_session.flush()
    
    coa = ChartOfAccounts(name="Main COA", tenant_id=tenant_id)
    db_session.add(coa)
    db_session.flush()
    cash_acc = Account(chart_of_accounts_id=coa.id, account_code="1000", name="Cash", account_type=AccountType.ASSET, tenant_id=tenant_id)
    rev_acc = Account(chart_of_accounts_id=coa.id, account_code="4000", name="Revenue", account_type=AccountType.REVENUE, tenant_id=tenant_id)
    db_session.add_all([cash_acc, rev_acc])
    db_session.flush()
    
    from app.models.bank import BankAccount
    bank = BankAccount(name="Main", account_number="123", bank_name="Test Bank", currency="USD", gl_account_id=cash_acc.id, tenant_id=tenant_id)
    db_session.add(bank)
    db_session.flush()
    
    ar_pay = Payment(
        reference="PAY-01",
        payment_type=PaymentType.AR_RECEIPT,
        date=date.today(),
        amount=Decimal("4000.00"),
        status=PaymentStatus.POSTED,
        client_id=client_ent.id,
        bank_account_id=bank.id,
        tenant_id=tenant_id
    )
    db_session.add(ar_pay)
    db_session.flush()
    ar_alloc = PaymentAllocation(
        payment_id=ar_pay.id,
        ar_invoice_id=ar_inv.id,
        amount=Decimal("4000.00"),
        tenant_id=tenant_id
    )
    db_session.add(ar_alloc)
    
    journal = Journal(date=date.today(), description="Test entry", status=JournalStatus.POSTED, tenant_id=tenant_id)
    db_session.add(journal)
    db_session.flush()
    jl1 = JournalLine(journal_id=journal.id, account_id=cash_acc.id, debit=Decimal("100.00"), credit=Decimal(0), tenant_id=tenant_id)
    jl2 = JournalLine(journal_id=journal.id, account_id=rev_acc.id, debit=Decimal(0), credit=Decimal("100.00"), tenant_id=tenant_id)
    db_session.add_all([jl1, jl2])

    db_session.commit()

    # Test Dashboard API
    res_dash = client.get(f"/api/v1/reports/projects/{project.id}/dashboard", headers=auth_headers)
    assert res_dash.status_code == 200
    dash = res_dash.json()
    assert Decimal(dash["contract_value"]) == Decimal("100000.00")
    assert Decimal(dash["billed"]) == Decimal("10000.00")
    assert Decimal(dash["collected"]) == Decimal("4000.00")
    assert Decimal(dash["receivable"]) == Decimal("6000.00")
    assert Decimal(dash["payable"]) == Decimal("1500.00")
    
    # Test AP Aging API
    res_ap = client.get("/api/v1/reports/accounting/ap-aging", headers=auth_headers)
    assert res_ap.status_code == 200
    ap = res_ap.json()
    assert Decimal(ap["totals"]["current"]) >= Decimal("1500.00")
    
    # Test Trial Balance API
    res_tb = client.get("/api/v1/reports/accounting/trial-balance", headers=auth_headers)
    assert res_tb.status_code == 200
    tb = res_tb.json()
    assert Decimal(tb["total_debit"]) >= Decimal("100.00")
    assert tb["total_debit"] == tb["total_credit"]
