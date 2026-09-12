import pytest
import uuid
from decimal import Decimal
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from app.models.warehouses import Warehouse
from app.models.materials import Material
from app.models.accounting import ChartOfAccounts, Account, AccountType
from app.models.contracts import Contract, ContractStatus
from app.models.projects import Project

@pytest.fixture
def two_tenants(db_session):
    t_a = Tenant(id=uuid.uuid4(), name="Tenant Alpha Construction")
    t_b = Tenant(id=uuid.uuid4(), name="Tenant Beta Builders")
    db_session.add_all([t_a, t_b])
    db_session.commit()

    u_a = User(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4()}@alpha.erp",
        hashed_password=get_password_hash("pw"),
        tenant_id=t_a.id,
        is_superuser=True
    )
    u_b = User(
        id=uuid.uuid4(),
        email=f"admin_{uuid.uuid4()}@beta.erp",
        hashed_password=get_password_hash("pw"),
        tenant_id=t_b.id,
        is_superuser=True
    )
    db_session.add_all([u_a, u_b])
    db_session.commit()

    token_a = create_access_token({"sub": str(u_a.id)})
    token_b = create_access_token({"sub": str(u_b.id)})

    headers_a = {"Authorization": f"Bearer {token_a}", "X-Tenant-ID": str(t_a.id)}
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Tenant-ID": str(t_b.id)}

    return {
        "tenant_a": t_a,
        "tenant_b": t_b,
        "user_a": u_a,
        "user_b": u_b,
        "headers_a": headers_a,
        "headers_b": headers_b,
    }

def test_tenant_isolation_clients_and_projects(client, two_tenants):
    h_a = two_tenants["headers_a"]
    h_b = two_tenants["headers_b"]

    # 1. Tenant A creates a client
    res = client.post(
        "/api/v1/clients/",
        headers=h_a,
        json={
            "name": "Alpha Prime Client",
            "legal_name": "Alpha Prime Client LLC",
            "contact_information": "contact@alphaprime.erp",
            "status": "ACTIVE"
        }
    )
    assert res.status_code == 201
    client_a_id = res.json()["id"]

    # 2. Tenant A creates a project linked to client
    res = client.post(
        "/api/v1/projects/",
        headers=h_a,
        json={
            "project_number": f"PRJ-A-{uuid.uuid4().hex[:6]}",
            "name": "Alpha Skyscraper Project",
            "client_id": client_a_id,
            "budget_amount": "5000000.00",
            "status": "ACTIVE"
        }
    )
    assert res.status_code == 201
    project_a_id = res.json()["id"]

    # 3. Tenant B queries clients - should NOT see Tenant A client
    res_b_clients = client.get("/api/v1/clients/", headers=h_b)
    assert res_b_clients.status_code == 200
    b_client_ids = [c["id"] for c in res_b_clients.json()]
    assert client_a_id not in b_client_ids

    # 4. Tenant B queries projects - should NOT see Tenant A project
    res_b_projects = client.get("/api/v1/projects/", headers=h_b)
    assert res_b_projects.status_code == 200
    b_proj_ids = [p["id"] for p in res_b_projects.json()]
    assert project_a_id not in b_proj_ids

    # 5. Tenant B attempts direct read of Tenant A project - should return 404
    res_direct = client.get(f"/api/v1/projects/{project_a_id}", headers=h_b)
    assert res_direct.status_code == 404

def test_inventory_ledger_transactions_and_balances(client, two_tenants, db_session):
    h_a = two_tenants["headers_a"]
    t_a = two_tenants["tenant_a"]

    # Setup warehouse and material for Tenant A
    wh = Warehouse(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        code=f"WH-{uuid.uuid4().hex[:4]}",
        name="Alpha Central Yard",
        type="CENTRAL"
    )
    mat = Material(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        material_code=f"MAT-{uuid.uuid4().hex[:4]}",
        name="Structural Rebar 20mm",
        base_unit="TON"
    )
    db_session.add_all([wh, mat])
    db_session.commit()

    # 1. Post stock intake of 50 TON via adjustments endpoint
    intake_res = client.post(
        "/api/v1/inventory/adjustments",
        headers=h_a,
        json={
            "adjustment_number": f"ADJ-{uuid.uuid4().hex[:6]}",
            "warehouse_id": str(wh.id),
            "date": "2026-09-07",
            "reason": "Initial yard stocking",
            "lines": [
                {
                    "material_id": str(mat.id),
                    "adjustment_type": "IN",
                    "quantity": 50.0,
                    "unit_cost": 850.00,
                    "notes": "Stock delivery"
                }
            ]
        }
    )
    assert intake_res.status_code == 200

    # 2. Verify detailed balance shows 50 TON and $42,500 valuation
    bal_res = client.get("/api/v1/inventory/balances/detail", headers=h_a)
    assert bal_res.status_code == 200
    balances = bal_res.json()
    item_bal = next((b for b in balances if b["material_id"] == str(mat.id)), None)
    assert item_bal is not None
    assert float(item_bal["quantity"]) == 50.0
    assert float(item_bal["total_cost"]) == 42500.0

    # 3. Post stock reduction of 20 TON (Adjustment OUT)
    out_res = client.post(
        "/api/v1/inventory/adjustments",
        headers=h_a,
        json={
            "adjustment_number": f"ADJ-{uuid.uuid4().hex[:6]}",
            "warehouse_id": str(wh.id),
            "date": "2026-09-07",
            "reason": "Site dispatch",
            "lines": [
                {
                    "material_id": str(mat.id),
                    "adjustment_type": "OUT",
                    "quantity": 20.0,
                    "unit_cost": 850.00,
                    "notes": "Dispatched to PRJ-101"
                }
            ]
        }
    )
    assert out_res.status_code == 200

    # 4. Verify balance is now exactly 30 TON (50 - 20)
    bal_res2 = client.get("/api/v1/inventory/balances/detail", headers=h_a)
    assert bal_res2.status_code == 200
    item_bal2 = next(b for b in bal_res2.json() if b["material_id"] == str(mat.id))
    assert float(item_bal2["quantity"]) == 30.0

    # 5. Verify immutable transaction ledger records both movements
    tx_res = client.get("/api/v1/inventory/transactions", headers=h_a)
    assert tx_res.status_code == 200
    txs = tx_res.json()
    assert len(txs) >= 2

def test_accounting_double_entry_balance_invariant(client, two_tenants, db_session):
    h_a = two_tenants["headers_a"]
    t_a = two_tenants["tenant_a"]

    # Setup Chart of Accounts and Accounts
    coa = ChartOfAccounts(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        name="Alpha Master COA"
    )
    db_session.add(coa)
    db_session.flush()

    acc_cash = Account(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        name="Operating Cash",
        account_code="1010",
        account_type=AccountType.ASSET,
        chart_of_accounts_id=coa.id
    )
    acc_rev = Account(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        name="Contract Revenue",
        account_code="4010",
        account_type=AccountType.REVENUE,
        chart_of_accounts_id=coa.id
    )
    db_session.add_all([acc_cash, acc_rev])
    db_session.commit()

    # 1. Attempt to post UNBALANCED journal entry ($1000 debit, $900 credit)
    bad_res = client.post(
        "/api/v1/accounting/journals",
        headers=h_a,
        json={
            "date": "2026-09-07",
            "description": "Unbalanced Journal Attempt",
            "lines": [
                {"account_id": str(acc_cash.id), "debit": "1000.00", "credit": "0.00"},
                {"account_id": str(acc_rev.id), "debit": "0.00", "credit": "900.00"}
            ]
        }
    )
    # Must be rejected (either 400 or ValueError unhandled)
    assert bad_res.status_code in [400, 422, 500]

    # 2. Post BALANCED journal entry ($1000 debit == $1000 credit)
    good_res = client.post(
        "/api/v1/accounting/journals",
        headers=h_a,
        json={
            "date": "2026-09-07",
            "description": "Initial Client Retainer Payment",
            "lines": [
                {"account_id": str(acc_cash.id), "debit": "1000.00", "credit": "0.00"},
                {"account_id": str(acc_rev.id), "debit": "0.00", "credit": "1000.00"}
            ]
        }
    )
    assert good_res.status_code in [200, 201]

    # 3. Verify Trial Balance reports debits == credits
    tb_res = client.get("/api/v1/reports/accounting/trial-balance", headers=h_a)
    assert tb_res.status_code == 200
    tb_data = tb_res.json()
    assert float(tb_data["total_debit"]) == float(tb_data["total_credit"])

def test_executive_dashboard_live_sql_aggregation(client, two_tenants, db_session):
    h_a = two_tenants["headers_a"]
    t_a = two_tenants["tenant_a"]

    # Add a project and active contract
    proj = Project(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        project_number="PRJ-DASH-001",
        name="Dash Tower Project",
        description="Dashboard Live Aggregation Test Project"
    )
    db_session.add(proj)
    db_session.flush()

    from app.models.contracts import ContractType
    ct = ContractType(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        name="Prime EPC",
        is_active=True
    )
    db_session.add(ct)
    db_session.flush()

    ctr = Contract(
        id=uuid.uuid4(),
        tenant_id=t_a.id,
        contract_number="CTR-DASH-001",
        project_id=proj.id,
        contract_type_id=ct.id,
        currency_code="USD",
        status=ContractStatus.ACTIVE,
        current_value=Decimal("4500000.00"),
        original_value=Decimal("4500000.00")
    )
    db_session.add(ctr)
    db_session.commit()

    # Query executive dashboard
    res = client.get("/api/v1/reports/executive-dashboard", headers=h_a)
    assert res.status_code == 200
    data = res.json()
    assert float(data["total_contract_value"]) >= 4500000.0
    assert data["total_active_contracts"] >= 1
    assert data["is_ledger_balanced"] is True

def test_full_business_workflow_lifecycle(client, two_tenants, db_session):
    h_a = two_tenants["headers_a"]
    t_a = two_tenants["tenant_a"]

    from app.models.accounting import ChartOfAccounts, Account
    from app.models.org_settings import AccountingPeriod, FiscalYear
    from datetime import date
    
    # 1. Setup master data and Accounts
    coa = ChartOfAccounts(id=uuid.uuid4(), tenant_id=t_a.id, name="E2E COA")
    db_session.add(coa)
    
    fy = FiscalYear(id=uuid.uuid4(), tenant_id=t_a.id, name="FY2026", start_date=date(2026,1,1), end_date=date(2026,12,31))
    db_session.add(fy)
    db_session.flush()
    
    ap = AccountingPeriod(id=uuid.uuid4(), fiscal_year_id=fy.id, tenant_id=t_a.id, name="2026-09", start_date=date(2026,9,1), end_date=date(2026,9,30), is_closed=False)
    db_session.add(ap)
    
    asset_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=t_a.id, account_code="1000", name="Inventory", account_type="ASSET")
    liab_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=t_a.id, account_code="2000", name="AP Liability", account_type="LIABILITY")
    exp_acc = Account(id=uuid.uuid4(), chart_of_accounts_id=coa.id, tenant_id=t_a.id, account_code="5000", name="Project Expense", account_type="EXPENSE")
    
    db_session.add_all([asset_acc, liab_acc, exp_acc])
    db_session.commit()

    client_res = client.post("/api/v1/clients/", headers=h_a, json={
        "name": "E2E Lifecycle Client",
        "legal_name": "E2E Lifecycle Client LLC",
        "contact_information": "contact@e2e.erp",
        "status": "ACTIVE"
    })
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    proj_res = client.post("/api/v1/projects/", headers=h_a, json={
        "project_number": f"PRJ-E2E-{uuid.uuid4().hex[:6]}",
        "name": "E2E Mega Project",
        "client_id": client_id,
        "budget_amount": "10000000.00",
        "status": "ACTIVE"
    })
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    wh_res = client.post("/api/v1/inventory/warehouses", headers=h_a, json={
        "code": f"WH-E2E-{uuid.uuid4().hex[:4]}",
        "name": "E2E Main Yard",
        "location": "Site A",
        "type": "CENTRAL"
    })
    assert wh_res.status_code == 201
    wh_id = wh_res.json()["id"]

    mat_res = client.post("/api/v1/inventory/materials", headers=h_a, json={
        "material_code": f"MAT-E2E-{uuid.uuid4().hex[:4]}",
        "name": "E2E Premium Cement",
        "category": "CONSTRUCTION_MATERIALS",
        "base_unit": "BAG",
        "description": "Premium Portland Cement"
    })
    assert mat_res.status_code == 201
    mat_id = mat_res.json()["id"]

    sup_res = client.post("/api/v1/suppliers/", headers=h_a, json={
        "name": "E2E Cement Co",
        "legal_name": "E2E Cement Company LLC",
        "contact_information": "sales@e2ecement.com",
        "status": "ACTIVE"
    })
    assert sup_res.status_code == 201
    sup_id = sup_res.json()["id"]

    cc_res = client.post("/api/v1/cost-codes", headers=h_a, json={
        "code": f"CC-E2E-{uuid.uuid4().hex[:4]}",
        "name": "Concrete Works",
        "category": "MATERIAL",
        "is_active": True
    })
    assert cc_res.status_code == 201
    cc_id = cc_res.json()["id"]

    # 2. Procurement (PO)
    po_res = client.post("/api/v1/purchase-orders/", headers=h_a, json={
        "po_number": f"PO-E2E-{uuid.uuid4().hex[:6]}",
        "project_id": project_id,
        "supplier_id": sup_id,
        "issue_date": "2026-09-01",
        "currency": "USD",
        "lines": [{
            "cost_code_id": cc_id,
            "item_description": "Premium Portland Cement",
            "unit": "BAG",
            "quantity": 1000,
            "unit_price": 10.00,
            "amount": 10000.00
        }]
    })
    if po_res.status_code != 201:
        print("PO ERror:", po_res.text)
    assert po_res.status_code == 201
    po_id = po_res.json()["id"]
    
    issue_po_res = client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=h_a)
    assert issue_po_res.status_code == 200
    
    # Get the PO line ID
    po_data = client.get(f"/api/v1/purchase-orders/{po_id}", headers=h_a).json()
    po_line_id = po_data["lines"][0]["id"]

    # 3. Inventory Receipt (GRN)
    grn_res = client.post("/api/v1/inventory/goods-receipts", headers=h_a, json={
        "receipt_number": f"GRN-E2E-{uuid.uuid4().hex[:6]}",
        "purchase_order_id": po_id,
        "supplier_id": sup_id,
        "warehouse_id": wh_id,
        "date": "2026-09-05",
        "lines": [{
            "purchase_order_line_id": po_line_id,
            "material_id": mat_id,
            "received_quantity": 1000,
            "accepted_quantity": 1000,
            "rejected_quantity": 0,
            "unit_cost": 10.00
        }]
    })
    assert grn_res.status_code == 200
    grn_id = grn_res.json()["id"]
    grn_line_id = grn_res.json()["lines"][0]["id"]

    # 4. Inventory Issue to Project
    issue_res = client.post("/api/v1/inventory/material-issues", headers=h_a, json={
        "issue_number": f"MI-E2E-{uuid.uuid4().hex[:6]}",
        "warehouse_id": wh_id,
        "project_id": project_id,
        "cost_code_id": cc_id,
        "date": "2026-09-06",
        "purpose": "Slab pour",
        "lines": [{
            "material_id": mat_id,
            "quantity": 500,
            "notes": "500 bags for slab"
        }]
    })
    assert issue_res.status_code == 200

    # 5. Accounts Payable Vendor Invoice
    inv_res = client.post("/api/v1/ap/invoices", headers=h_a, json={
        "number": f"INV-E2E-{uuid.uuid4().hex[:6]}",
        "supplier_id": sup_id,
        "purchase_order_id": po_id,
        "goods_receipt_id": grn_id,
        "date": "2026-09-07",
        "due_date": "2026-10-07",
        "invoice_type": "STANDARD",
        "currency": "USD",
        "description": "Invoice for Cement",
        "tax_amount": 0.00,
        "lines": [{
            "project_id": project_id,
            "cost_code_id": cc_id,
            "purchase_order_line_id": po_line_id,
            "goods_receipt_line_id": grn_line_id,
            "material_id": mat_id,
            "description": "Premium Portland Cement",
            "quantity": 1000,
            "unit_price": 10.00,
            "tax_amount": 0.00
        }]
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # 6. Three-way match
    match_res = client.post(f"/api/v1/ap/invoices/{inv_id}/match", headers=h_a)
    assert match_res.status_code == 200
    assert match_res.json()["is_matched"] is True

    # 7. Approve & Post AP Invoice
    approve_res = client.post(f"/api/v1/ap/invoices/{inv_id}/approve", headers=h_a)
    assert approve_res.status_code == 200
    post_res = client.post(f"/api/v1/ap/invoices/{inv_id}/post", headers=h_a)
    if post_res.status_code != 200:
        print("POST Error:", post_res.text)
    assert post_res.status_code == 200

    # 8. Check General Ledger Balance
    tb_res = client.get("/api/v1/reports/accounting/trial-balance", headers=h_a)
    assert tb_res.status_code == 200
    tb_data = tb_res.json()
    assert float(tb_data["total_debit"]) == float(tb_data["total_credit"])

    # 9. Verify Project Cost KPIs (Ensuring no double counting!)
    # We issued 500 bags @ $10 = $5,000 ACTUAL cost.
    # The AP Invoice was for $10,000 (1000 bags) but it shouldn't hit Project Cost directly since it's an inventory material.
    kpi_res = client.get(f"/api/v1/reports/projects/{project_id}/dashboard", headers=h_a)
    assert kpi_res.status_code == 200
    kpi_data = kpi_res.json()
    
    # We expect actual cost to be 5000 (Material Issue). 
    assert float(kpi_data["actual_cost"]) == 5000.0
    # We expect committed cost to be 10000 (Purchase Order).
    assert float(kpi_data["committed_cost"]) == 10000.0

    print("End-to-End Business Workflow Completed Successfully!")
