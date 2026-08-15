from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.hr import (
    HRDepartment, Position, Employee, ProjectAssignment,
    Timesheet, TimesheetLine, TimesheetStatus
)
from app.schemas.hr import (
    DepartmentCreate, DepartmentResponse,
    PositionCreate, PositionResponse,
    EmployeeCreate, EmployeeResponse,
    ProjectAssignmentCreate, ProjectAssignmentResponse,
    TimesheetCreate, TimesheetResponse
)
from app.services.hr_service import HRService

router = APIRouter()

# -----------------------------------------------------------------------------
# Departments
# -----------------------------------------------------------------------------
@router.post("/departments", response_model=DepartmentResponse, status_code=201)
def create_department(
    data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept = HRDepartment(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(HRDepartment).filter(HRDepartment.tenant_id == current_user.tenant_id).all()


# -----------------------------------------------------------------------------
# Positions
# -----------------------------------------------------------------------------
@router.post("/positions", response_model=PositionResponse, status_code=201)
def create_position(
    data: PositionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pos = Position(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(pos)
    db.commit()
    db.refresh(pos)
    return pos

@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Position).filter(Position.tenant_id == current_user.tenant_id).all()


# -----------------------------------------------------------------------------
# Employees
# -----------------------------------------------------------------------------
@router.post("/employees", response_model=EmployeeResponse, status_code=201)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    emp = Employee(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp

@router.get("/employees", response_model=List[EmployeeResponse])
def get_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Employee).filter(Employee.tenant_id == current_user.tenant_id).all()


# -----------------------------------------------------------------------------
# Project Assignments
# -----------------------------------------------------------------------------
@router.post("/assignments", response_model=ProjectAssignmentResponse, status_code=201)
def create_assignment(
    data: ProjectAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = ProjectAssignment(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/assignments", response_model=List[ProjectAssignmentResponse])
def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(ProjectAssignment).filter(ProjectAssignment.tenant_id == current_user.tenant_id).all()


# -----------------------------------------------------------------------------
# Timesheets
# -----------------------------------------------------------------------------
@router.post("/timesheets", response_model=TimesheetResponse, status_code=201)
def create_timesheet(
    data: TimesheetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ts_data = data.model_dump(exclude={"lines"})
    ts = Timesheet(**ts_data, tenant_id=current_user.tenant_id)
    db.add(ts)
    db.flush()

    for line_data in data.lines:
        line = TimesheetLine(**line_data.model_dump(), timesheet_id=ts.id, tenant_id=current_user.tenant_id)
        db.add(line)

    db.commit()
    db.refresh(ts)
    return ts

@router.get("/timesheets/{timesheet_id}", response_model=TimesheetResponse)
def get_timesheet(
    timesheet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ts = db.query(Timesheet).filter(
        Timesheet.tenant_id == current_user.tenant_id,
        Timesheet.id == timesheet_id
    ).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Timesheet not found")
    return ts

@router.post("/timesheets/{timesheet_id}/submit", response_model=TimesheetResponse)
def submit_timesheet(
    timesheet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = HRService(db, current_user.tenant_id, current_user.id)
    return service.submit_timesheet(timesheet_id)

@router.post("/timesheets/{timesheet_id}/approve", response_model=TimesheetResponse)
def approve_timesheet(
    timesheet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = HRService(db, current_user.tenant_id, current_user.id)
    return service.approve_timesheet(timesheet_id)
