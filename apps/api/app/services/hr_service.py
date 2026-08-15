from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from decimal import Decimal
from fastapi import HTTPException

from app.models.hr import (
    Timesheet, TimesheetLine, TimesheetStatus,
    ProjectAssignment, Employee
)

class HRService:
    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def _get_applicable_rate(self, employee_id: UUID, project_id: UUID, date_worked: date) -> Decimal:
        # Check for project assignment override
        assignment = self.db.execute(
            select(ProjectAssignment)
            .where(
                ProjectAssignment.tenant_id == self.tenant_id,
                ProjectAssignment.employee_id == employee_id,
                ProjectAssignment.project_id == project_id,
                ProjectAssignment.start_date <= date_worked,
                (ProjectAssignment.end_date >= date_worked) | (ProjectAssignment.end_date == None)
            )
        ).scalar_one_or_none()

        if assignment and assignment.hourly_rate_override is not None:
            return assignment.hourly_rate_override

        # Fallback to employee base rate
        employee = self.db.execute(
            select(Employee)
            .where(
                Employee.tenant_id == self.tenant_id,
                Employee.id == employee_id
            )
        ).scalar_one_or_none()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        return employee.base_hourly_rate

    def submit_timesheet(self, timesheet_id: UUID) -> Timesheet:
        timesheet = self.db.execute(
            select(Timesheet)
            .where(
                Timesheet.tenant_id == self.tenant_id,
                Timesheet.id == timesheet_id
            )
        ).scalar_one_or_none()

        if not timesheet:
            raise HTTPException(status_code=404, detail="Timesheet not found")
        
        if timesheet.status != TimesheetStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT timesheets can be submitted")
            
        timesheet.status = TimesheetStatus.SUBMITTED
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet

    def approve_timesheet(self, timesheet_id: UUID) -> Timesheet:
        timesheet = self.db.execute(
            select(Timesheet)
            .where(
                Timesheet.tenant_id == self.tenant_id,
                Timesheet.id == timesheet_id
            )
        ).scalar_one_or_none()

        if not timesheet:
            raise HTTPException(status_code=404, detail="Timesheet not found")

        if timesheet.status != TimesheetStatus.SUBMITTED:
            raise HTTPException(status_code=400, detail="Only SUBMITTED timesheets can be approved")

        # Lock in rates and calculate cost for each line
        # Assuming standard 1.5x for overtime
        for line in timesheet.lines:
            rate = self._get_applicable_rate(timesheet.employee_id, line.project_id, line.date)
            line.hourly_rate = rate
            
            reg_cost = line.regular_hours * rate
            ot_cost = line.overtime_hours * (rate * Decimal("1.5"))
            line.total_cost = reg_cost + ot_cost

        timesheet.status = TimesheetStatus.APPROVED
        self.db.commit()
        self.db.refresh(timesheet)
        return timesheet
