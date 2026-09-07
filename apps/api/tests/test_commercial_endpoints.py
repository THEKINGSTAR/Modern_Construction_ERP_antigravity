import pytest
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4
from app.models.org_settings import FiscalYear, AccountingPeriod
from app.models.accounting import ChartOfAccounts, Account, AccountType

def test_commercial_extended_endpoints(client, test_user, db_session, auth_headers):
    # 1. Project setup
    project_data = {
        "project_number": f"PROJ-COMM-{uuid4().hex[:6]}",
        "name": "Tower Commercial Package",
        "status": "ACTIVE"
    }
    proj_resp = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # 2. Client & Contract setup
    client_data = {"name": f"Developer Client {uuid4().hex[:4]}", "client_code": f"CL-{uuid4().hex[:4]}"}
    client_resp = client.post("/api/v1/clients/", json=client_data, headers=auth_headers)
    assert client_resp.status_code == 201
    client_id = client_resp.json()["id"]

    ctype_id = client.post("/api/v1/contracts/types/", json={"name": "GMP Guaranteed Max", "is_active": True}, headers=auth_headers).json()["id"]

    contract_data = {
        "project_id": project_id,
        "client_id": client_id,
        "contract_number": f"CTR-EXT-{uuid4().hex[:6]}",
        "contract_type_id": ctype_id,
        "original_value": 5000000.0,
        "currency_code": "USD"
    }
    contract_resp = client.post("/api/v1/contracts/", json=contract_data, headers=auth_headers)
    assert contract_resp.status_code == 201
    contract_id = contract_resp.json()["id"]

    # 3. Supplier setup
    supplier_data = {"name": "Titan Steel Subcontractor", "supplier_code": f"SUPP-{uuid4().hex[:4]}"}
    supp_resp = client.post("/api/v1/suppliers/", json=supplier_data, headers=auth_headers)
    assert supp_resp.status_code == 201
    supplier_id = supp_resp.json()["id"]

    # 4. Create Subcontract
    sc_data = {
        "project_id": project_id,
        "supplier_id": supplier_id,
        "subcontract_number": f"SC-STEEL-{uuid4().hex[:6]}",
        "original_value": 850000.0,
        "currency_code": "USD",
        "retention_rate": 10.0,
        "start_date": "2026-02-01",
        "end_date": "2026-11-30"
    }
    sc_create_resp = client.post("/api/v1/commercial/subcontracts", json=sc_data, headers=auth_headers)
    assert sc_create_resp.status_code == 201
    subcontract_id = sc_create_resp.json()["id"]
    assert float(sc_create_resp.json()["current_value"]) == 850000.0

    # 5. List Subcontracts & Get Subcontract Detail
    sc_list_resp = client.get(f"/api/v1/commercial/subcontracts?project_id={project_id}", headers=auth_headers)
    assert sc_list_resp.status_code == 200
    subcontracts = sc_list_resp.json()
    assert len(subcontracts) >= 1
    assert any(s["id"] == subcontract_id for s in subcontracts)

    sc_detail_resp = client.get(f"/api/v1/commercial/subcontracts/{subcontract_id}", headers=auth_headers)
    assert sc_detail_resp.status_code == 200
    assert sc_detail_resp.json()["subcontract_number"] == sc_data["subcontract_number"]
    assert sc_detail_resp.json()["supplier_name"] == "Titan Steel Subcontractor"

    # 6. Subcontract Change Order lifecycle
    sco_data = {
        "subcontract_id": subcontract_id,
        "number": "SCO-001",
        "title": "Additional Structural Bracing",
        "amount": 45000.0,
        "description": "Seismic bracing for level 14-20"
    }
    sco_create_resp = client.post("/api/v1/commercial/subcontract-change-orders", json=sco_data, headers=auth_headers)
    assert sco_create_resp.status_code == 201
    sco_id = sco_create_resp.json()["id"]
    assert sco_create_resp.json()["status"] == "DRAFT"

    sco_list_resp = client.get(f"/api/v1/commercial/subcontract-change-orders?subcontract_id={subcontract_id}", headers=auth_headers)
    assert sco_list_resp.status_code == 200
    assert len(sco_list_resp.json()) >= 1

    sco_approve_resp = client.post(f"/api/v1/commercial/subcontract-change-orders/{sco_id}/approve", headers=auth_headers)
    assert sco_approve_resp.status_code == 200
    assert sco_approve_resp.json()["status"] == "APPROVED"

    # Verify subcontract current value increased by 45,000 (850,000 + 45,000 = 895,000)
    sc_recheck = client.get(f"/api/v1/commercial/subcontracts/{subcontract_id}", headers=auth_headers)
    assert float(sc_recheck.json()["current_value"]) == 895000.0

    # 7. Fiscal Year & Accounting Period in Settings
    fy = FiscalYear(tenant_id=test_user.tenant_id, name="FY2026-TEST", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db_session.add(fy)
    db_session.flush()

    period = AccountingPeriod(
        tenant_id=test_user.tenant_id,
        fiscal_year_id=fy.id,
        name="Period 2026-09",
        start_date=date(2026, 9, 1),
        end_date=date(2026, 9, 30),
        is_closed=False
    )
    db_session.add(period)
    db_session.commit()

    periods_resp = client.get("/api/v1/settings/accounting-periods", headers=auth_headers)
    assert periods_resp.status_code == 200
    assert any(p["name"] == "Period 2026-09" for p in periods_resp.json())

    # 8. Commercial Summary Endpoint
    summary_resp = client.get("/api/v1/commercial/summary", headers=auth_headers)
    assert summary_resp.status_code == 200
    sum_data = summary_resp.json()
    assert float(sum_data["total_prime_contract_value"]) >= 5000000.0
    assert float(sum_data["total_subcontracts_value"]) >= 895000.0
    assert float(sum_data["total_subcontract_change_orders_approved"]) >= 45000.0
    assert sum_data["subcontracts_count"] >= 1
