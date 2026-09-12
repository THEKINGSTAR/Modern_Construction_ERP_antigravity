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

def test_equipment_fleet_summary_and_enriched_listing(client: TestClient, db_session: Session, auth_headers, test_tenant):
    # 1. Summary
    res = client.get("/api/v1/equipment/summary", headers=auth_headers)
    assert res.status_code == 200
    summary = res.json()
    assert "total_units" in summary
    assert "available_units" in summary
    assert "in_use_units" in summary
    assert "maintenance_units" in summary
    assert "utilization_rate" in summary
    assert "total_operating_hours" in summary
    assert "total_fuel_cost" in summary
    assert "total_maintenance_cost" in summary
    assert "total_equipment_cost" in summary
    assert summary["total_units"] >= 0

    # 2. Detailed listing
    res_list = client.get("/api/v1/equipment/", headers=auth_headers)
    assert res_list.status_code == 200
    eq_list = res_list.json()
    assert isinstance(eq_list, list)
    if len(eq_list) > 0:
        first = eq_list[0]
        assert "total_operating_hours" in first
        assert "total_fuel_cost" in first
        assert "total_maintenance_cost" in first

def test_equipment_crud_and_status_patch(client: TestClient, db_session: Session, auth_headers, test_tenant):
    unique_id = f"EQ-TEST-{uuid4().hex[:6].upper()}"
    create_payload = {
        "name": "Test Hydraulic Excavator",
        "make": "TestMfg",
        "model": "TX-300",
        "year": "2024",
        "serial_number": f"SN-{unique_id}",
        "internal_id": unique_id,
        "status": "AVAILABLE",
        "base_hourly_cost": "175.50"
    }
    create_res = client.post("/api/v1/equipment/", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["internal_id"] == unique_id
    assert created["status"] == "AVAILABLE"
    eq_id = created["id"]

    # Patch status to MAINTENANCE
    patch_res = client.patch(f"/api/v1/equipment/{eq_id}", json={
        "status": "MAINTENANCE",
        "base_hourly_cost": "180.00"
    }, headers=auth_headers)
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["status"] == "MAINTENANCE"
    assert float(patched["base_hourly_cost"]) == 180.00

def test_equipment_assignment_and_dispatch(client: TestClient, db_session: Session, auth_headers, test_tenant):
    project = Project(
        name="Fleet Dispatch Project",
        project_number=f"PRJ-EQ-{uuid4().hex[:4]}",
        status=ProjectStatus.ACTIVE,
        tenant_id=test_tenant.id
    )
    db_session.add(project)
    
    eq = Equipment(
        name="Fleet Mobile Crane",
        internal_id=f"EQ-CRN-{uuid4().hex[:4]}",
        status=EquipmentStatus.AVAILABLE,
        base_hourly_cost=Decimal("350.00"),
        tenant_id=test_tenant.id
    )
    db_session.add(eq)
    db_session.commit()

    # Create assignment
    assign_payload = {
        "equipment_id": str(eq.id),
        "project_id": str(project.id),
        "start_date": "2026-03-01",
        "hourly_cost_override": "375.00"
    }
    res = client.post("/api/v1/equipment/assignments", json=assign_payload, headers=auth_headers)
    assert res.status_code == 201
    created_assign = res.json()
    assert created_assign["equipment_id"] == str(eq.id)
    assert float(created_assign["hourly_cost_override"]) == 375.00

    # Verify equipment status transitioned to IN_USE
    updated_eq = db_session.query(Equipment).filter(Equipment.id == eq.id).first()
    assert updated_eq.status == EquipmentStatus.IN_USE

    # List assignments
    list_res = client.get("/api/v1/equipment/assignments", headers=auth_headers)
    assert list_res.status_code == 200
    assignments = list_res.json()
    found = next((a for a in assignments if a["id"] == created_assign["id"]), None)
    assert found is not None
    assert found["project_name"] == project.name
    assert found["equipment_name"] == eq.name

def test_equipment_usage_logs_workflow_and_cost_rate_lock(client: TestClient, db_session: Session, auth_headers, test_tenant):
    project = Project(
        name="Site Earthworks Alpha",
        project_number=f"PRJ-EW-{uuid4().hex[:4]}",
        status=ProjectStatus.ACTIVE,
        tenant_id=test_tenant.id
    )
    db_session.add(project)
    
    cc = CostCode(
        code=f"02-{uuid4().hex[:4]}",
        name="Site Excavation",
        tenant_id=test_tenant.id
    )
    db_session.add(cc)

    eq = Equipment(
        name="Heavy Earthmover",
        internal_id=f"EQ-EM-{uuid4().hex[:4]}",
        status=EquipmentStatus.IN_USE,
        base_hourly_cost=Decimal("150.00"),
        tenant_id=test_tenant.id
    )
    db_session.add(eq)
    db_session.commit()

    # Assignment with override
    assignment = EquipmentAssignment(
        equipment_id=eq.id,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        hourly_cost_override=Decimal("165.00"),
        tenant_id=test_tenant.id
    )
    db_session.add(assignment)
    db_session.commit()

    # Create Usage Log
    log_payload = {
        "equipment_id": str(eq.id),
        "period_start": "2026-03-01",
        "period_end": "2026-03-07",
        "lines": [
            {
                "project_id": str(project.id),
                "cost_code_id": str(cc.id),
                "date": "2026-03-02",
                "hours": "12.5"
            },
            {
                "project_id": str(project.id),
                "cost_code_id": str(cc.id),
                "date": "2026-03-04",
                "hours": "7.5"
            }
        ]
    }
    create_log_res = client.post("/api/v1/equipment/usage-logs", json=log_payload, headers=auth_headers)
    assert create_log_res.status_code == 201
    log_id = create_log_res.json()["id"]

    # Submit
    sub_res = client.post(f"/api/v1/equipment/usage-logs/{log_id}/submit", headers=auth_headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "SUBMITTED"

    # Approve
    app_res = client.post(f"/api/v1/equipment/usage-logs/{log_id}/approve", headers=auth_headers)
    assert app_res.status_code == 200
    approved_log = app_res.json()
    assert approved_log["status"] == "APPROVED"
    assert len(approved_log["lines"]) == 2
    # 12.5 hrs * $165 = $2062.50
    assert float(approved_log["lines"][0]["hourly_cost_rate"]) == 165.00
    assert float(approved_log["lines"][0]["total_cost"]) == 2062.50
    # 7.5 hrs * $165 = $1237.50
    assert float(approved_log["lines"][1]["total_cost"]) == 1237.50

    # List usage logs
    list_logs_res = client.get("/api/v1/equipment/usage-logs", headers=auth_headers)
    assert list_logs_res.status_code == 200
    logs = list_logs_res.json()
    found_log = next((l for l in logs if l["id"] == log_id), None)
    assert found_log is not None
    assert float(found_log["total_hours"]) == 20.0
    assert float(found_log["total_cost"]) == 3300.0

def test_fuel_and_maintenance_records_with_details(client: TestClient, db_session: Session, auth_headers, test_tenant):
    project = Project(
        name="Site Logistics Beta",
        project_number=f"PRJ-LG-{uuid4().hex[:4]}",
        status=ProjectStatus.ACTIVE,
        tenant_id=test_tenant.id
    )
    db_session.add(project)
    
    cc = CostCode(
        code=f"01-{uuid4().hex[:4]}",
        name="Temporary Equipment Power",
        tenant_id=test_tenant.id
    )
    db_session.add(cc)

    eq = Equipment(
        name="Site Power Generator",
        internal_id=f"EQ-GEN-{uuid4().hex[:4]}",
        status=EquipmentStatus.AVAILABLE,
        base_hourly_cost=Decimal("50.00"),
        tenant_id=test_tenant.id
    )
    db_session.add(eq)
    db_session.commit()

    # 1. Fuel Transaction
    fuel_payload = {
        "equipment_id": str(eq.id),
        "project_id": str(project.id),
        "cost_code_id": str(cc.id),
        "date": "2026-03-05",
        "volume": "150.0",
        "unit_cost": "3.80"
    }
    fuel_res = client.post("/api/v1/equipment/fuel", json=fuel_payload, headers=auth_headers)
    assert fuel_res.status_code == 201
    assert float(fuel_res.json()["total_cost"]) == 570.00

    # List fuel
    fuel_list_res = client.get("/api/v1/equipment/fuel", headers=auth_headers)
    assert fuel_list_res.status_code == 200
    fuels = fuel_list_res.json()
    found_fuel = next((f for f in fuels if f["id"] == fuel_res.json()["id"]), None)
    assert found_fuel is not None
    assert found_fuel["equipment_name"] == eq.name
    assert found_fuel["project_name"] == project.name

    # 2. Maintenance Record (CORRECTIVE)
    maint_payload = {
        "equipment_id": str(eq.id),
        "project_id": str(project.id),
        "cost_code_id": str(cc.id),
        "type": "CORRECTIVE",
        "date": "2026-03-08",
        "description": "Alternator replacement due to electrical surge",
        "duration_hours": "8.0",
        "cost": "850.00"
    }
    maint_res = client.post("/api/v1/equipment/maintenance", json=maint_payload, headers=auth_headers)
    assert maint_res.status_code == 201

    # Verify equipment status transitioned to MAINTENANCE
    updated_eq = db_session.query(Equipment).filter(Equipment.id == eq.id).first()
    assert updated_eq.status == EquipmentStatus.MAINTENANCE

    # List maintenance
    maint_list_res = client.get("/api/v1/equipment/maintenance", headers=auth_headers)
    assert maint_list_res.status_code == 200
    maints = maint_list_res.json()
    found_maint = next((m for m in maints if m["id"] == maint_res.json()["id"]), None)
    assert found_maint is not None
    assert found_maint["equipment_name"] == eq.name
    assert found_maint["type"] == "CORRECTIVE"
