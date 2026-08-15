import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hr import (
    HRDepartment, Position, Employee, ProjectAssignment,
    Timesheet, TimesheetLine, TimesheetStatus
)
from app.models.projects import Project, ProjectStatus
from app.models.cost_codes import CostCode

def test_workforce_timesheet_and_labor_cost(client: TestClient, db_session: Session, auth_headers, test_tenant):
    tenant_id = test_tenant.id

    # 1. Setup Cost Codes & Project
    project = Project(
        name="HR Project",
        project_number="HR-01",
        status=ProjectStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(project)
    
    cc = CostCode(
        code="LBR-01",
        name="Direct Labor",
        tenant_id=tenant_id
    )
    db_session.add(cc)
    db_session.flush()

    # 2. Setup HR entities
    dept_res = client.post("/api/v1/hr/departments", json={"name": "Engineering"}, headers=auth_headers)
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]

    pos_res = client.post("/api/v1/hr/positions", json={"title": "Site Engineer"}, headers=auth_headers)
    assert pos_res.status_code == 201
    pos_id = pos_res.json()["id"]

    # 3. Create Employee
    emp_res = client.post("/api/v1/hr/employees", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "department_id": dept_id,
        "position_id": pos_id,
        "base_hourly_rate": "50.00"
    }, headers=auth_headers)
    assert emp_res.status_code == 201
    emp_id = emp_res.json()["id"]

    # 4. Project Assignment
    assign_res = client.post("/api/v1/hr/assignments", json={
        "employee_id": emp_id,
        "project_id": str(project.id),
        "role": "Lead Engineer",
        "start_date": "2026-01-01",
        "hourly_rate_override": "60.00"
    }, headers=auth_headers)
    assert assign_res.status_code == 201

    # 5. Create Timesheet
    ts_res = client.post("/api/v1/hr/timesheets", json={
        "employee_id": emp_id,
        "period_start": "2026-01-01",
        "period_end": "2026-01-07",
        "lines": [
            {
                "project_id": str(project.id),
                "cost_code_id": str(cc.id),
                "date": "2026-01-02",
                "regular_hours": "8.0",
                "overtime_hours": "2.0"
            }
        ]
    }, headers=auth_headers)
    assert ts_res.status_code == 201
    ts_id = ts_res.json()["id"]

    # 6. Submit Timesheet
    sub_res = client.post(f"/api/v1/hr/timesheets/{ts_id}/submit", headers=auth_headers)
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "SUBMITTED"

    # Verify project cost is STILL 0 because timesheet is not approved yet
    cost_res1 = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/summary", headers=auth_headers)
    assert cost_res1.status_code == 200
    # No cost summary yet or zero
    if len(cost_res1.json()) > 0:
        assert float(cost_res1.json()[0]["actual_cost"]) == 0.0

    # 7. Approve Timesheet
    app_res = client.post(f"/api/v1/hr/timesheets/{ts_id}/approve", headers=auth_headers)
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"
    
    # Let's check computed total cost
    app_lines = app_res.json()["lines"]
    assert len(app_lines) == 1
    # 8 hrs * $60 (override rate) = 480
    # 2 hrs OT * $60 * 1.5 = 180
    # Total = 660
    assert float(app_lines[0]["total_cost"]) == 660.0

    # 8. Verify Project Cost
    cost_res2 = client.get(f"/api/v1/project-cost/projects/{project.id}/costs/summary", headers=auth_headers)
    assert cost_res2.status_code == 200
    summaries = cost_res2.json()
    assert len(summaries) == 1
    assert float(summaries[0]["actual_cost"]) == 660.0

def test_timesheet_fallback_rate(client: TestClient, db_session: Session, auth_headers, test_tenant):
    tenant_id = test_tenant.id

    # Create Project & CC
    project = Project(
        name="HR Project 2",
        project_number="HR-02",
        status=ProjectStatus.ACTIVE,
        tenant_id=tenant_id
    )
    db_session.add(project)
    
    cc = CostCode(
        code="LBR-02",
        name="Direct Labor",
        tenant_id=tenant_id
    )
    db_session.add(cc)
    db_session.flush()

    # Create Employee without assignment rate override
    emp_res = client.post("/api/v1/hr/employees", json={
        "first_name": "Jane",
        "last_name": "Smith",
        "base_hourly_rate": "40.00"
    }, headers=auth_headers)
    emp_id = emp_res.json()["id"]

    # Timesheet
    ts_res = client.post("/api/v1/hr/timesheets", json={
        "employee_id": emp_id,
        "period_start": "2026-02-01",
        "period_end": "2026-02-07",
        "lines": [
            {
                "project_id": str(project.id),
                "cost_code_id": str(cc.id),
                "date": "2026-02-02",
                "regular_hours": "10.0" # 10 * 40 = 400
            }
        ]
    }, headers=auth_headers)
    ts_id = ts_res.json()["id"]

    client.post(f"/api/v1/hr/timesheets/{ts_id}/submit", headers=auth_headers)
    app_res = client.post(f"/api/v1/hr/timesheets/{ts_id}/approve", headers=auth_headers)
    
    assert float(app_res.json()["lines"][0]["total_cost"]) == 400.0
