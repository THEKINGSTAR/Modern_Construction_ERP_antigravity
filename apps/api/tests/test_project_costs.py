import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.projects import Project, ProjectStatus
from app.models.cost_codes import CostCode
from app.models.budgets import Budget, BudgetLine
from app.models.suppliers import Supplier
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.warehouses import Warehouse
from app.models.materials import Material
from app.models.inventory import InventoryTransaction, InventoryBalance, TransactionType
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from sqlalchemy import text

def test_project_cost_engine_full_lifecycle(client: TestClient, db_session: Session, auth_headers, test_tenant):
    # Setup data
    tenant_id = test_tenant.id

    # 1. Project & Cost Code
    project = Project(
        name="Cost Test Project",
        project_number="PRJ-COST-01",
        status=ProjectStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(project)
    db_session.flush()

    cc = CostCode(
        code="CC-COST",
        name="Cost Code",
        tenant_id=tenant_id
    )
    db_session.add(cc)
    db_session.flush()

    # 2. Budget (1000)
    budget = Budget(
        project_id=project.id,
        budget_number="BUD-01",
        status="APPROVED",
        tenant_id=tenant_id
    )
    db_session.add(budget)
    db_session.flush()
    b_line = BudgetLine(
        budget_id=budget.id,
        cost_code_id=cc.id,
        original_budget=Decimal("1000.00"),
        approved_changes=Decimal("0.00"),
        tenant_id=tenant_id
    )
    db_session.add(b_line)
    db_session.flush()

    # 3. Purchase Order -> Committed Cost (200)
    supplier = Supplier(name="Test Supplier", code="SUPP-01", tenant_id=tenant_id)
    db_session.add(supplier)
    db_session.flush()
    po = PurchaseOrder(
        po_number="PO-COST-01",
        project_id=project.id,
        supplier_id=supplier.id,
        status=POStatus.ISSUED,
        issue_date=date.today(),
        currency="USD",
        tenant_id=tenant_id
    )
    db_session.add(po)
    db_session.flush()
    po_line = PurchaseOrderLine(
        purchase_order_id=po.id,
        cost_code_id=cc.id,
        item_description="Test Item",
        unit="EA",
        quantity=Decimal("10"),
        unit_price=Decimal("20.00"),
        amount=Decimal("200.00"),
        tenant_id=tenant_id
    )
    db_session.add(po_line)
    db_session.flush()

    # 4. Material Issue -> Actual Cost (100)
    warehouse = Warehouse(name="Cost WH", code="WH-COST", tenant_id=tenant_id)
    db_session.add(warehouse)
    material = Material(name="Cost Mat", item_code="MAT-COST", base_unit="EA", tenant_id=tenant_id)
    db_session.add(material)
    db_session.flush()
    
    # We must post the Material Issue so it counts as ACTUAL cost
    issue = MaterialIssue(
        issue_number="ISS-COST-01",
        warehouse_id=warehouse.id,
        project_id=project.id,
        cost_code_id=cc.id,
        date=date.today(),
        status=MaterialIssueStatus.POSTED,
        tenant_id=tenant_id
    )
    db_session.add(issue)
    db_session.flush()
    issue_line = MaterialIssueLine(
        material_issue_id=issue.id,
        material_id=material.id,
        quantity=Decimal("5"),
        unit_cost=Decimal("20.00"), # 5 * 20 = 100
        tenant_id=tenant_id
    )
    db_session.add(issue_line)
    db_session.commit()

    # 5. Check Transactions endpoint
    res_txn = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/transactions", headers=auth_headers)
    assert res_txn.status_code == 200
    txns = res_txn.json()
    assert len(txns) == 2
    
    # Find COMMITTED
    committed_txn = next(t for t in txns if t["cost_type"] == "COMMITTED")
    assert committed_txn["amount"] == "200.00"
    
    # Find ACTUAL
    actual_txn = next(t for t in txns if t["cost_type"] == "ACTUAL")
    assert actual_txn["amount"] == "100.00"

    # 6. Add ETC via Forecast (ETC = 750)
    res_fc = client.post(
        f"/api/v1/project-cost/projects/{project.id}/forecasts",
        headers=auth_headers,
        json={
            "forecast_number": "FC-01",
            "date": str(date.today()),
            "lines": [
                {
                    "cost_code_id": str(cc.id),
                    "etc_amount": "750.00"
                }
            ]
        }
    )
    assert res_fc.status_code == 201

    # 7. Check Summary endpoint
    res_sum = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/summary", headers=auth_headers)
    assert res_sum.status_code == 200
    summaries = res_sum.json()
    assert len(summaries) == 1
    
    summary = summaries[0]
    assert summary["original_budget"] == "1000.00"
    assert summary["current_budget"] == "1000.00"
    assert summary["committed_cost"] == "200.00"
    assert summary["actual_cost"] == "100.00"
    assert summary["estimate_to_complete"] == "750.00"
    
    # EAC = Actual + ETC = 100 + 750 = 850
    assert summary["estimate_at_completion"] == "850.00"
    
    # Variance = Current Budget - EAC = 1000 - 850 = 150
    assert summary["variance"] == "150.00"
