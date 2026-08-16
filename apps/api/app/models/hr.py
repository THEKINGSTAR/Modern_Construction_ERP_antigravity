import enum
import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class TimesheetStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class LeaveType(str, enum.Enum):
    VACATION = "VACATION"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    OTHER = "OTHER"

class HRDepartment(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "hr_departments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    manager_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL", use_alter=True, name="fk_hr_departments_manager_id"), nullable=True)

class Position(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "positions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

class Employee(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "employees"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    department_id = Column(Uuid(as_uuid=True), ForeignKey("hr_departments.id", ondelete="SET NULL"), nullable=True)
    position_id = Column(Uuid(as_uuid=True), ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)
    base_hourly_rate = Column(Numeric(18, 4), nullable=False, default=0)
    
    department = relationship("HRDepartment", foreign_keys=[department_id])
    position = relationship("Position")

class ProjectAssignment(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "project_assignments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(100), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    hourly_rate_override = Column(Numeric(18, 4), nullable=True)

    employee = relationship("Employee")
    project = relationship("Project")

class LeaveRequest(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "leave_requests"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(Enum(LeaveType, native_enum=False), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatus, native_enum=False), default=LeaveStatus.PENDING, nullable=False)
    notes = Column(Text, nullable=True)

    employee = relationship("Employee")

class Timesheet(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "timesheets"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(Uuid(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(Enum(TimesheetStatus, native_enum=False), default=TimesheetStatus.DRAFT, nullable=False)
    
    employee = relationship("Employee")
    lines = relationship("TimesheetLine", back_populates="timesheet", cascade="all, delete-orphan")

class TimesheetLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "timesheet_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timesheet_id = Column(Uuid(as_uuid=True), ForeignKey("timesheets.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    regular_hours = Column(Numeric(10, 4), nullable=False, default=0)
    overtime_hours = Column(Numeric(10, 4), nullable=False, default=0)
    
    # Locked in upon approval
    hourly_rate = Column(Numeric(18, 4), nullable=True)
    total_cost = Column(Numeric(18, 4), nullable=True)

    timesheet = relationship("Timesheet", back_populates="lines")
    project = relationship("Project")
    cost_code = relationship("CostCode")
