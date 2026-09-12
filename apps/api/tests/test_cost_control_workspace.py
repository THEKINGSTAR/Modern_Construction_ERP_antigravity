import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.projects import Project, ProjectStatus
from app.models.cost_codes import CostCode, CostCategory
from app.models.budgets import Budget, BudgetLine
from app.models.suppliers import Supplier, SupplierStatus
from app.models.warehouses import Warehouse, WarehouseType
from app.models.materials import Material
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from app.models.forecasts import ProjectForecast, ProjectForecastLine, ForecastStatus

@pytest.fixture
def cost_control_setup(db_session: Session, test_user):
    tenant_id = test_user.tenant_id

    # 1. Project
    project = Project(
        id=uuid.uuid4(),
        name="Cost Control Test Project",
        project_number="PRJ-CC-01",
        status=ProjectStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(project)

    # 2. Supplier
    supplier = Supplier(
        id=uuid.uuid4(),
        name="Global Concrete Supplies",
        status=SupplierStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(supplier)

    # 3. Warehouse & Material
    warehouse = Warehouse(
        id=uuid.uuid4(),
        code="WH-CC-01",
        name="Cost Control Warehouse",
        type=WarehouseType.CENTRAL,
        tenant_id=tenant_id
    )
    material = Material(
        id=uuid.uuid4(),
        material_code="MAT-CONC-01",
        name="Ready Mix Concrete C30",
        base_unit="M3",
        tenant_id=tenant_id
    )
    db_session.add_all([warehouse, material])

    # 4. Cost Codes
    cc_mat = CostCode(
        id=uuid.uuid4(),
        code="03-3000-TEST",
        name="Concrete Cast-in-Place Test",
        category=CostCategory.MATERIAL,
        tenant_id=tenant_id
    )
    cc_sub = CostCode(
        id=uuid.uuid4(),
        code="05-1200-TEST",
        name="Structural Steel Test",
        category=CostCategory.SUBCONTRACT,
        tenant_id=tenant_id
    )
    db_session.add_all([cc_mat, cc_sub])
    db_session.flush()

    # 5. Budget with lines
    budget = Budget(
        id=uuid.uuid4(),
        name="Test Cost Budget",
        status="APPROVED",
        project_id=project.id,
        tenant_id=tenant_id
    )
    db_session.add(budget)
    db_session.flush()

    bl_mat = BudgetLine(
        id=uuid.uuid4(),
        budget_id=budget.id,
        cost_code_id=cc_mat.id,
        original_budget=Decimal("500000.00"),
        approved_changes=Decimal("50000.00"),
        tenant_id=tenant_id
    )
    bl_sub = BudgetLine(
        id=uuid.uuid4(),
        budget_id=budget.id,
        cost_code_id=cc_sub.id,
        original_budget=Decimal("300000.00"),
        approved_changes=Decimal("0.00"),
        tenant_id=tenant_id
    )
    db_session.add_all([bl_mat, bl_sub])

    # 6. Committed Cost: Purchase Order (Issued)
    po = PurchaseOrder(
        id=uuid.uuid4(),
        po_number="PO-CC-TEST-001",
        project_id=project.id,
        supplier_id=supplier.id,
        tenant_id=tenant_id,
        status=POStatus.ISSUED,
        issue_date=date.today(),
        currency="USD"
    )
    db_session.add(po)
    db_session.flush()

    po_line = PurchaseOrderLine(
        id=uuid.uuid4(),
        purchase_order_id=po.id,
        cost_code_id=cc_mat.id,
        item_description="Ready-mix concrete",
        unit="M3",
        quantity=Decimal("100"),
        unit_price=Decimal("1500.00"),
        amount=Decimal("150000.00"),
        tenant_id=tenant_id
    )
    db_session.add(po_line)

    # 7. Actual Cost: Material Issue (Posted)
    mi = MaterialIssue(
        id=uuid.uuid4(),
        issue_number="MI-CC-TEST-001",
        warehouse_id=warehouse.id,
        project_id=project.id,
        cost_code_id=cc_mat.id,
        date=date.today(),
        status=MaterialIssueStatus.POSTED,
        tenant_id=tenant_id
    )
    db_session.add(mi)
    db_session.flush()

    mi_line = MaterialIssueLine(
        id=uuid.uuid4(),
        material_issue_id=mi.id,
        material_id=material.id,
        quantity=Decimal("20"),
        unit_cost=Decimal("1500.00"),
        tenant_id=tenant_id
    )
    db_session.add(mi_line)

    db_session.commit()

    return {
        "tenant_id": tenant_id,
        "project": project,
        "cc_mat": cc_mat,
        "cc_sub": cc_sub,
        "budget": budget,
        "po": po,
        "mi": mi
    }

def test_portfolio_cost_summary(client: TestClient, auth_headers, cost_control_setup):
    res = client.get("/api/v1/project-cost/portfolio/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_projects" in data
    assert data["total_projects"] >= 1
    assert "total_budget" in data
    assert "total_committed" in data
    assert "total_actual" in data
    assert "total_etc" in data
    assert "total_eac" in data
    assert "total_variance" in data
    assert "overall_cpi" in data
    assert isinstance(data["projects"], list)

def test_project_cost_summary(client: TestClient, auth_headers, cost_control_setup):
    project_id = str(cost_control_setup["project"].id)
    res = client.get(f"/api/v1/project-cost/projects/{project_id}/costs/summary", headers=auth_headers)
    assert res.status_code == 200
    summaries = res.json()
    assert len(summaries) >= 2

    # Find concrete cost code summary
    mat_summary = next((s for s in summaries if s["cost_code_code"] == "03-3000-TEST"), None)
    assert mat_summary is not None
    assert Decimal(str(mat_summary["original_budget"])) == Decimal("500000.00")
    assert Decimal(str(mat_summary["approved_changes"])) == Decimal("50000.00")
    assert Decimal(str(mat_summary["current_budget"])) == Decimal("550000.00")
    assert Decimal(str(mat_summary["committed_cost"])) == Decimal("150000.00")
    assert Decimal(str(mat_summary["actual_cost"])) == Decimal("30000.00") # 20 * 1500

def test_project_cost_kpis(client: TestClient, auth_headers, cost_control_setup):
    project_id = str(cost_control_setup["project"].id)
    res = client.get(f"/api/v1/project-cost/projects/{project_id}/costs/kpi", headers=auth_headers)
    assert res.status_code == 200
    kpi = res.json()
    assert kpi["project_id"] == project_id
    assert kpi["project_name"] == "Cost Control Test Project"
    assert Decimal(str(kpi["total_current_budget"])) == Decimal("850000.00") # 550k + 300k
    assert Decimal(str(kpi["total_committed"])) == Decimal("150000.00")
    assert Decimal(str(kpi["total_actual"])) == Decimal("30000.00")
    assert "status" in kpi

def test_project_cost_transactions_audit(client: TestClient, auth_headers, cost_control_setup):
    project_id = str(cost_control_setup["project"].id)
    res = client.get(f"/api/v1/project-cost/projects/{project_id}/costs/transactions", headers=auth_headers)
    assert res.status_code == 200
    txns = res.json()
    assert len(txns) >= 2 # 1 PO, 1 Material Issue

    po_txn = next((t for t in txns if t["source_type"] == "PURCHASE_ORDER"), None)
    assert po_txn is not None
    assert Decimal(str(po_txn["amount"])) == Decimal("150000.00")
    assert po_txn["cost_type"] == "COMMITTED"
    assert po_txn["source_reference"] == "PO-CC-TEST-001"

    mi_txn = next((t for t in txns if t["source_type"] == "MATERIAL_ISSUE"), None)
    assert mi_txn is not None
    assert Decimal(str(mi_txn["amount"])) == Decimal("30000.00")
    assert mi_txn["cost_type"] == "ACTUAL"

def test_create_project_forecast_and_rollup(client: TestClient, auth_headers, cost_control_setup):
    project_id = str(cost_control_setup["project"].id)
    cc_mat_id = str(cost_control_setup["cc_mat"].id)
    cc_sub_id = str(cost_control_setup["cc_sub"].id)

    payload = {
        "forecast_number": "FC-TEST-001",
        "date": "2026-03-01",
        "notes": "Q1 ETC Adjustment Test",
        "lines": [
            {
                "cost_code_id": cc_mat_id,
                "etc_amount": "120000.00",
                "notes": "Remaining concrete pours"
            },
            {
                "cost_code_id": cc_sub_id,
                "etc_amount": "280000.00",
                "notes": "Remaining steel erection"
            }
        ]
    }

    res = client.post(f"/api/v1/project-cost/projects/{project_id}/forecasts", json=payload, headers=auth_headers)
    assert res.status_code == 201
    assert res.json()["status"] == "APPROVED"

    # Verify rollup in cost summary
    summary_res = client.get(f"/api/v1/project-cost/projects/{project_id}/costs/summary", headers=auth_headers)
    assert summary_res.status_code == 200
    summaries = summary_res.json()

    mat_s = next((s for s in summaries if s["cost_code_id"] == cc_mat_id), None)
    assert mat_s is not None
    assert Decimal(str(mat_s["estimate_to_complete"])) == Decimal("120000.00")
    # EAC = AC + ETC = 30000 + 120000 = 150000
    assert Decimal(str(mat_s["estimate_at_completion"])) == Decimal("150000.00")
    # Variance = Budget - EAC = 550000 - 150000 = 400000 (UNDER_BUDGET)
    assert Decimal(str(mat_s["variance"])) == Decimal("400000.00")
    assert mat_s["status"] == "UNDER_BUDGET"
