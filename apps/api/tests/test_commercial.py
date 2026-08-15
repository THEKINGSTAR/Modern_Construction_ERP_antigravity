import pytest
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4
from app.models.org_settings import FiscalYear, AccountingPeriod
from app.models.accounting import ChartOfAccounts, Account, AccountType, Journal, JournalLine

def test_subcontract_lifecycle_and_payment_app(client, test_user, db_session, auth_headers):
    # Setup test dependencies
    # 1. Project
    project_data = {
        "project_number": f"PROJ-{uuid4().hex[:6]}",
        "name": "Commercial Project",
        "description": "Test Project",
        "status": "ACTIVE"
    }
    proj_resp = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Supplier
    supplier_data = {
        "name": "Acme Subcontractors",
        "supplier_code": f"SUB-{uuid4().hex[:6]}"
    }
    supp_resp = client.post("/api/v1/suppliers/", json=supplier_data, headers=auth_headers)
    assert supp_resp.status_code == 201
    supplier_id = supp_resp.json()["id"]

    # 3. Create Subcontract
    subcontract_data = {
        "project_id": project_id,
        "supplier_id": supplier_id,
        "subcontract_number": f"SC-{uuid4().hex[:6]}",
        "original_value": 100000.0,
        "currency_code": "USD",
        "retention_rate": 10.0,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31"
    }
    sc_resp = client.post("/api/v1/commercial/subcontracts", json=subcontract_data, headers=auth_headers)
    assert sc_resp.status_code == 201
    sc_id = sc_resp.json()["id"]

    # 4. Accounting setup (Period + Accounts)
    fy = FiscalYear(tenant_id=test_user.tenant_id, name="FY2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db_session.add(fy)
    db_session.flush()
    fy_id = fy.id
    
    period = AccountingPeriod(
        tenant_id=test_user.tenant_id,
        fiscal_year_id=fy.id,
        name="P1",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        is_closed=False
    )
    db_session.add(period)
    db_session.flush()
    period_id = period.id
    
    coa = ChartOfAccounts(tenant_id=test_user.tenant_id, name="Comm COA")
    db_session.add(coa)
    db_session.flush()
    coa_id = coa.id

    wip_account = Account(tenant_id=test_user.tenant_id, chart_of_accounts_id=coa.id, account_code=f"WIP-{uuid4().hex[:4]}", name="WIP", account_type=AccountType.ASSET)
    ap_account = Account(tenant_id=test_user.tenant_id, chart_of_accounts_id=coa.id, account_code=f"AP-{uuid4().hex[:4]}", name="Accounts Payable", account_type=AccountType.LIABILITY)
    retention_account = Account(tenant_id=test_user.tenant_id, chart_of_accounts_id=coa.id, account_code=f"RET-{uuid4().hex[:4]}", name="Retention Payable", account_type=AccountType.LIABILITY)
    
    db_session.add_all([wip_account, ap_account, retention_account])
    db_session.flush()

    wip_account_id = wip_account.id
    ap_account_id = ap_account.id
    retention_account_id = retention_account.id

    # 5. Create Subcontract Payment Application
    app_data = {
        "subcontract_id": sc_id,
        "accounting_period_id": str(period_id),
        "number": "APP-001",
        "date": "2026-01-31",
        "gross_work": 50000.0,
        "previous_certified_work": 0.0,
        "retention_amount": 5000.0, # 10%
        "advance_recovery_amount": 0.0,
        "deductions_amount": 0.0,
        "adjustments_amount": 0.0
    }
    app_resp = client.post("/api/v1/commercial/subcontract-payment-applications", json=app_data, headers=auth_headers)
    assert app_resp.status_code == 201
    app_id = app_resp.json()["id"]
    assert float(app_resp.json()["net_amount_due"]) == 45000.0

    # 6. Approve App
    approve_resp = client.post(f"/api/v1/commercial/subcontract-payment-applications/{app_id}/approve", headers=auth_headers)
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

    # 7. Post App
    post_resp = client.post(
        f"/api/v1/commercial/subcontract-payment-applications/{app_id}/post"
        f"?wip_account_id={wip_account_id}&ap_account_id={ap_account_id}&retention_account_id={retention_account_id}",
        headers=auth_headers
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["status"] == "POSTED"
    
    journal_id = post_resp.json()["journal_id"]
    assert journal_id is not None

    # 8. Check GL
    journal = db_session.query(Journal).filter(Journal.id == UUID(journal_id)).first()
    assert journal is not None
    assert journal.status == "POSTED"
    
    lines = db_session.query(JournalLine).filter(JournalLine.journal_id == UUID(journal_id)).all()
    assert len(lines) == 3 # WIP (Debit), AP (Credit), Retention (Credit)
    
    debits = sum(float(l.debit) for l in lines)
    credits = sum(float(l.credit) for l in lines)
    assert debits == 50000.0
    assert credits == 50000.0

def test_client_change_order_lifecycle(client, test_user, db_session, auth_headers):
    # Setup
    client_data = {"name": "Big Client", "client_code": f"C-{uuid4().hex[:6]}"}
    client_id = client.post("/api/v1/clients/", json=client_data, headers=auth_headers).json()["id"]
    
    proj_id = client.post("/api/v1/projects/", json={"project_number": f"P-{uuid4().hex[:6]}", "name": "P1", "status": "ACTIVE"}, headers=auth_headers).json()["id"]
    
    ctype_id = client.post("/api/v1/contracts/types/", json={"name": "Lump Sum", "is_active": True}, headers=auth_headers).json()["id"]
    
    contract_data = {
        "project_id": proj_id,
        "client_id": client_id,
        "contract_number": f"CTR-{uuid4().hex[:6]}",
        "contract_type_id": ctype_id,
        "original_value": 1000000.0,
        "currency_code": "USD"
    }
    contract_resp = client.post("/api/v1/contracts/", json=contract_data, headers=auth_headers)
    assert contract_resp.status_code == 201
    contract_id = contract_resp.json()["id"]
    
    # Verify original value
    assert float(contract_resp.json()["current_value"]) == 1000000.0

    # Create CCO
    cco_data = {
        "contract_id": contract_id,
        "number": "CCO-01",
        "title": "Extra Work",
        "amount": 50000.0
    }
    cco_resp = client.post("/api/v1/commercial/client-change-orders", json=cco_data, headers=auth_headers)
    assert cco_resp.status_code == 201
    cco_id = cco_resp.json()["id"]

    # Approve CCO
    app_cco_resp = client.post(f"/api/v1/commercial/client-change-orders/{cco_id}/approve", headers=auth_headers)
    assert app_cco_resp.status_code == 200

    # Re-fetch contract to check current value
    contract_get = client.get(f"/api/v1/contracts/{contract_id}", headers=auth_headers)
    assert float(contract_get.json()["current_value"]) == 1050000.0
