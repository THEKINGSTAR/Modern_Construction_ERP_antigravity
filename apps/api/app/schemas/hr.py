from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.models.hr import TimesheetStatus, LeaveStatus, LeaveType

class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    manager_id: Optional[UUID] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class PositionBase(BaseModel):
    title: str = Field(..., max_length=100)
    description: Optional[str] = None

class PositionCreate(PositionBase):
    pass

class PositionResponse(PositionBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    department_id: Optional[UUID] = None
    position_id: Optional[UUID] = None
    base_hourly_rate: Decimal = Field(default=0, ge=0)

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class ProjectAssignmentBase(BaseModel):
    employee_id: UUID
    project_id: UUID
    role: Optional[str] = Field(None, max_length=100)
    start_date: date
    end_date: Optional[date] = None
    hourly_rate_override: Optional[Decimal] = Field(None, ge=0)

class ProjectAssignmentCreate(ProjectAssignmentBase):
    pass

class ProjectAssignmentResponse(ProjectAssignmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class LeaveRequestBase(BaseModel):
    employee_id: UUID
    leave_type: LeaveType
    start_date: date
    end_date: date
    notes: Optional[str] = None

class LeaveRequestCreate(LeaveRequestBase):
    pass

class LeaveRequestResponse(LeaveRequestBase):
    id: UUID
    status: LeaveStatus
    model_config = ConfigDict(from_attributes=True)


class TimesheetLineBase(BaseModel):
    project_id: UUID
    cost_code_id: UUID
    date: date
    regular_hours: Decimal = Field(default=0, ge=0)
    overtime_hours: Decimal = Field(default=0, ge=0)

class TimesheetLineCreate(TimesheetLineBase):
    pass

class TimesheetLineResponse(TimesheetLineBase):
    id: UUID
    timesheet_id: UUID
    hourly_rate: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)


class TimesheetBase(BaseModel):
    employee_id: UUID
    period_start: date
    period_end: date

class TimesheetCreate(TimesheetBase):
    lines: List[TimesheetLineCreate] = []

class TimesheetResponse(TimesheetBase):
    id: UUID
    status: TimesheetStatus
    lines: List[TimesheetLineResponse] = []
    model_config = ConfigDict(from_attributes=True)
