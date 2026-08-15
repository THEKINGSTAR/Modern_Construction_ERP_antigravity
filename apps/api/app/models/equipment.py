import enum
import uuid
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class EquipmentStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"

class UsageLogStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"

class MaintenanceType(str, enum.Enum):
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"

class Equipment(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "equipment"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    make = Column(String(100), nullable=True)
    model = Column(String(100), nullable=True)
    year = Column(String(4), nullable=True)
    serial_number = Column(String(100), nullable=True)
    internal_id = Column(String(100), nullable=True, index=True)
    
    status = Column(Enum(EquipmentStatus, native_enum=False), default=EquipmentStatus.AVAILABLE, nullable=False)
    base_hourly_cost = Column(Numeric(18, 4), nullable=False, default=0)

class EquipmentAssignment(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "equipment_assignments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(Uuid(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    hourly_cost_override = Column(Numeric(18, 4), nullable=True)

    equipment = relationship("Equipment")
    project = relationship("Project")

class EquipmentUsageLog(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "equipment_usage_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(Uuid(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(Enum(UsageLogStatus, native_enum=False), default=UsageLogStatus.DRAFT, nullable=False)
    
    equipment = relationship("Equipment")
    lines = relationship("EquipmentUsageLine", back_populates="usage_log", cascade="all, delete-orphan")

class EquipmentUsageLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "equipment_usage_lines"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usage_log_id = Column(Uuid(as_uuid=True), ForeignKey("equipment_usage_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    hours = Column(Numeric(10, 4), nullable=False, default=0)
    
    # Locked in upon approval
    hourly_cost_rate = Column(Numeric(18, 4), nullable=True)
    total_cost = Column(Numeric(18, 4), nullable=True)

    usage_log = relationship("EquipmentUsageLog", back_populates="lines")
    project = relationship("Project")
    cost_code = relationship("CostCode")

class FuelTransaction(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "fuel_transactions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(Uuid(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="SET NULL"), nullable=True, index=True)
    
    date = Column(Date, nullable=False)
    volume = Column(Numeric(10, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    total_cost = Column(Numeric(18, 4), nullable=False)

    equipment = relationship("Equipment")
    project = relationship("Project")
    cost_code = relationship("CostCode")

class MaintenanceRecord(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "maintenance_records"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    equipment_id = Column(Uuid(as_uuid=True), ForeignKey("equipment.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="SET NULL"), nullable=True, index=True)
    
    type = Column(Enum(MaintenanceType, native_enum=False), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    duration_hours = Column(Numeric(10, 4), nullable=True)
    cost = Column(Numeric(18, 4), nullable=False, default=0)

    equipment = relationship("Equipment")
    project = relationship("Project")
    cost_code = relationship("CostCode")
