import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.equipment import (
    Equipment, EquipmentAssignment, EquipmentUsageLog, EquipmentUsageLine,
    FuelTransaction, MaintenanceRecord, EquipmentStatus, UsageLogStatus, MaintenanceType
)
from app.models.projects import Project, ProjectStatus
from app.models.cost_codes import CostCode

def test_equipment_management_and_project_cost(client: TestClient, db_session: Session, auth_headers, test_tenant):
    tenant_id = test_tenant.id

    # 1. Setup Cost Codes & Project
    project = Project(
        name="Equipment Project",
        project_number="EQP-01",
        status=ProjectStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(project)
    
    cc = CostCode(
        code="EQP-001",
        name="Heavy Machinery",
        tenant_id=tenant_id
    )
    db_session.add(cc)
    db_session.flush()

    # 2. Create Equipment
    eq_res = client.post("/api/v1/equipment/", json={
        "name": "Excavator 320",
        "make": "Caterpillar",
        "model": "320",
        "year": "2020",
        "base_hourly_cost": "150.00"
    }, headers=auth_headers)
    assert eq_res.status_code == 201
    eq_id = eq_res.json()["id"]

    # 3. Create Equipment Assignment
    assign_res = client.post("/api/v1/equipment/assignments", json={
        "equipment_id": eq_id,
        "project_id": str(project.id),
        "start_date": "2026-01-01",
        "hourly_cost_override": "200.00"
    }, headers=auth_headers)
    assert assign_res.status_code == 201

    # 4. Create Usage Log
    usage_res = client.post("/api/v1/equipment/usage-logs", json={
        "equipment_id": eq_id,
        "period_start": "2026-01-01",
        "period_end": "2026-01-07",
        "lines": [
            {
                "project_id": str(project.id),
                "cost_code_id": str(cc.id),
                "date": "2026-01-02",
                "hours": "10.0"
            }
        ]
    }, headers=auth_headers)
    assert usage_res.status_code == 201
    log_id = usage_res.json()["id"]

    # Verify project cost is 0 before approval
    cost_res1 = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/summary", headers=auth_headers)
    if len(cost_res1.json()) > 0:
        assert float(cost_res1.json()[0]["actual_cost"]) == 0.0

    # Submit & Approve Usage Log
    sub_res = client.post(f"/api/v1/equipment/usage-logs/{log_id}/submit", headers=auth_headers)
    assert sub_res.status_code == 200

    app_res = client.post(f"/api/v1/equipment/usage-logs/{log_id}/approve", headers=auth_headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"
    assert float(app_res.json()["lines"][0]["total_cost"]) == 2000.0  # 10 hrs * 200 (override)

    # 5. Create Fuel Transaction
    fuel_res = client.post("/api/v1/equipment/fuel", json={
        "equipment_id": eq_id,
        "project_id": str(project.id),
        "cost_code_id": str(cc.id),
        "date": "2026-01-03",
        "volume": "100.0",
        "unit_cost": "1.50"
    }, headers=auth_headers)
    assert fuel_res.status_code == 201
    assert float(fuel_res.json()["total_cost"]) == 150.0

    # 6. Create Maintenance Record
    maint_res = client.post("/api/v1/equipment/maintenance", json={
        "equipment_id": eq_id,
        "project_id": str(project.id),
        "cost_code_id": str(cc.id),
        "type": "PREVENTIVE",
        "date": "2026-01-05",
        "description": "Oil Change",
        "cost": "500.00"
    }, headers=auth_headers)
    assert maint_res.status_code == 201

    # 7. Verify Project Cost
    cost_res2 = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/summary", headers=auth_headers)
    assert cost_res2.status_code == 200
    summaries = cost_res2.json()
    assert len(summaries) == 1
    
    # Total Cost = 2000 (Usage) + 150 (Fuel) + 500 (Maintenance) = 2650.0
    assert float(summaries[0]["actual_cost"]) == 2650.0
