import pytest
from uuid import uuid4
from datetime import date
from decimal import Decimal
from fastapi.testclient import TestClient

from app.models.tenant import Tenant
from app.models.accounting import ChartOfAccounts, Account, AccountType, Journal, JournalLine, JournalStatus
from app.models.projects import Project, ProjectStatus
from app.models.clients import Client
from app.models.suppliers import Supplier
from app.models.cost_codes import CostCode
from app.models.commercial import ClientPaymentApplication, PaymentAppStatus
from app.models.contracts import Contract, ContractType, ContractStatus
from app.models.warehouses import Warehouse
from app.models.materials import Material
from app.models.inventory import InventoryTransaction, TransactionType, InventoryBalance
from app.models.ap_ar import APInvoice, APInvoiceLine, InvoiceStatus, Payment, PaymentType, PaymentStatus, PaymentAllocation

# Use the same setup as other tests for test_tenant and auth_headers
def test_tenant_isolation(db_session):
    # Create two tenants
    tenant1 = Tenant(id=uuid4(), name="Tenant A")
    tenant2 = Tenant(id=uuid4(), name="Tenant B")
    db_session.add_all([tenant1, tenant2])
    db_session.flush()

    # Create projects in both
    p1 = Project(name="Project A", project_number="PA-01", status=ProjectStatus.ACTIVE, tenant_id=tenant1.id)
    p2 = Project(name="Project B", project_number="PB-01", status=ProjectStatus.ACTIVE, tenant_id=tenant2.id)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Query using Tenant A
    projects_a = db_session.query(Project).filter(Project.tenant_id == tenant1.id).all()
    assert len(projects_a) == 1
    assert projects_a[0].id == p1.id

    # Query using Tenant B
    projects_b = db_session.query(Project).filter(Project.tenant_id == tenant2.id).all()
    assert len(projects_b) == 1
    assert projects_b[0].id == p2.id


def test_accounting_golden_rule(db_session, test_tenant):
    tenant_id = test_tenant.id

    coa = ChartOfAccounts(name="Golden COA", tenant_id=tenant_id)
    db_session.add(coa)
    db_session.flush()

    acc1 = Account(chart_of_accounts_id=coa.id, account_code="1000", name="Cash", account_type=AccountType.ASSET, tenant_id=tenant_id)
    acc2 = Account(chart_of_accounts_id=coa.id, account_code="2000", name="AP", account_type=AccountType.LIABILITY, tenant_id=tenant_id)
    acc3 = Account(chart_of_accounts_id=coa.id, account_code="4000", name="Revenue", account_type=AccountType.REVENUE, tenant_id=tenant_id)
    acc4 = Account(chart_of_accounts_id=coa.id, account_code="5000", name="COGS", account_type=AccountType.EXPENSE, tenant_id=tenant_id)
    db_session.add_all([acc1, acc2, acc3, acc4])
    db_session.flush()

    # Create a perfectly balancing journal
    journal = Journal(date=date.today(), description="Sales Entry", status=JournalStatus.POSTED, tenant_id=tenant_id)
    db_session.add(journal)
    db_session.flush()

    lines = [
        JournalLine(journal_id=journal.id, account_id=acc1.id, debit=Decimal("5000.00"), credit=Decimal("0.00"), tenant_id=tenant_id),
        JournalLine(journal_id=journal.id, account_id=acc3.id, debit=Decimal("0.00"), credit=Decimal("5000.00"), tenant_id=tenant_id),
        JournalLine(journal_id=journal.id, account_id=acc4.id, debit=Decimal("2000.00"), credit=Decimal("0.00"), tenant_id=tenant_id),
        JournalLine(journal_id=journal.id, account_id=acc2.id, debit=Decimal("0.00"), credit=Decimal("2000.00"), tenant_id=tenant_id),
    ]
    db_session.add_all(lines)
    db_session.commit()

    # Verify Golden Rule
    debits = sum([l.debit for l in lines])
    credits = sum([l.credit for l in lines])
    assert debits == credits
    assert debits == Decimal("7000.00")

    # DB Level Check
    from sqlalchemy import select, func
    res = db_session.execute(
        select(func.sum(JournalLine.debit), func.sum(JournalLine.credit)).where(JournalLine.journal_id == journal.id)
    ).first()
    assert res[0] == res[1]


def test_inventory_golden_rule(db_session, test_tenant):
    tenant_id = test_tenant.id

    wh = Warehouse(name="Main WH", code="WH01", location="Central", tenant_id=tenant_id)
    mat = Material(material_code="MAT01", name="Steel", base_unit="KG", active=True, tenant_id=tenant_id)
    db_session.add_all([wh, mat])
    db_session.flush()

    # 1. Receipt
    print(f"wh.id type: {type(wh.id)}, value: {wh.id}")
    print(f"mat.id type: {type(mat.id)}, value: {mat.id}")
    
    tx1 = InventoryTransaction(
        warehouse_id=wh.id,
        material_id=mat.id,
        transaction_type=TransactionType.RECEIPT,
        quantity=Decimal("100.00"),
        unit_cost=Decimal("2.50"),
        total_cost=Decimal("250.00"),
        transaction_date=date.today(),
        reference_type="PO",
        reference_id=uuid4(),
        tenant_id=tenant_id
    )
    db_session.add(tx1)
    
    bal = InventoryBalance(
        warehouse_id=wh.id,
        material_id=mat.id,
        quantity=Decimal("100.00"),
        total_cost=Decimal("250.00"),
        tenant_id=tenant_id
    )
    db_session.add(bal)
    db_session.commit()

    # 2. Issue
    tx2 = InventoryTransaction(
        warehouse_id=wh.id,
        material_id=mat.id,
        transaction_type=TransactionType.ISSUE,
        quantity=Decimal("40.00"),
        unit_cost=Decimal("2.50"),
        total_cost=Decimal("100.00"),
        transaction_date=date.today(),
        reference_type="PROJECT",
        reference_id=uuid4(),
        tenant_id=tenant_id
    )
    db_session.add(tx2)
    bal.quantity -= Decimal("40.00")
    bal.total_cost -= Decimal("100.00")
    db_session.commit()

    # Verify Golden Rule (No negative stock)
    assert bal.quantity == Decimal("60.00")
    assert bal.quantity >= 0

    # Verify audit trail sum
    from sqlalchemy import select, func, case
    res = db_session.execute(
        select(
            func.sum(
                case(
                    (InventoryTransaction.transaction_type == TransactionType.RECEIPT, InventoryTransaction.quantity),
                    (InventoryTransaction.transaction_type == TransactionType.ISSUE, -InventoryTransaction.quantity),
                    else_=0
                )
            )
        ).where(InventoryTransaction.material_id == mat.id)
    ).scalar()
    
    assert res == bal.quantity

def test_project_lifecycle_e2e(client: TestClient, db_session, auth_headers, test_tenant):
    tenant_id = test_tenant.id

    # 1. Base Setup
    project = Project(name="E2E Project", project_number="E2E-01", status=ProjectStatus.ACTIVE, tenant_id=tenant_id)
    client_ent = Client(name="E2E Client", tenant_id=tenant_id)
    supplier_ent = Supplier(name="E2E Supplier", tenant_id=tenant_id)
    cc = CostCode(code="E2E-CC", name="E2E Code", tenant_id=tenant_id)
    db_session.add_all([project, client_ent, supplier_ent, cc])
    db_session.flush()

    ctype = ContractType(name="Fixed", tenant_id=tenant_id)
    db_session.add(ctype)
    db_session.flush()

    # 2. Contract
    contract = Contract(
        project_id=project.id,
        client_id=client_ent.id,
        contract_number="CTR-E2E-01",
        contract_type_id=ctype.id,
        original_value=Decimal("500000.00"),
        current_value=Decimal("500000.00"),
        currency_code="USD",
        status=ContractStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(contract)
    db_session.commit()

    # 3. Simulate AP Invoice
    ap_inv = APInvoice(
        number="AP-E2E-01",
        supplier_id=supplier_ent.id,
        date=date.today(),
        due_date=date.today(),
        status=InvoiceStatus.POSTED,
        total_amount=Decimal("25000.00"),
        tenant_id=tenant_id
    )
    db_session.add(ap_inv)
    db_session.flush()
    ap_line = APInvoiceLine(
        invoice_id=ap_inv.id,
        project_id=project.id,
        cost_code_id=cc.id,
        description="E2E Work",
        unit_price=Decimal("25000.00"),
        line_total=Decimal("25000.00"),
        tenant_id=tenant_id
    )
    db_session.add(ap_line)
    db_session.commit()

    # 4. Check Dashboard API
    res = client.get(f"/api/v1/reports/projects/{project.id}/dashboard", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert float(data["contract_value"]) == 500000.0
    assert float(data["payable"]) == 25000.0
