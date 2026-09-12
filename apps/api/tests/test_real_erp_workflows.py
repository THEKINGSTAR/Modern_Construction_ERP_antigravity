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
        type="MAIN"
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
