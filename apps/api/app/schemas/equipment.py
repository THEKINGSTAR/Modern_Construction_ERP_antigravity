from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import date
from typing import Optional, List
from decimal import Decimal
from app.models.equipment import EquipmentStatus, UsageLogStatus, MaintenanceType

# -----------------------------------------------------------------------------
# Equipment
# -----------------------------------------------------------------------------
class EquipmentBase(BaseModel):
    name: str = Field(..., max_length=255)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[str] = Field(None, max_length=4)
    serial_number: Optional[str] = Field(None, max_length=100)
    internal_id: Optional[str] = Field(None, max_length=100)
    status: EquipmentStatus = EquipmentStatus.AVAILABLE
    base_hourly_cost: Decimal

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    year: Optional[str] = Field(None, max_length=4)
    serial_number: Optional[str] = Field(None, max_length=100)
    internal_id: Optional[str] = Field(None, max_length=100)
    status: Optional[EquipmentStatus] = None
    base_hourly_cost: Optional[Decimal] = None

class EquipmentResponse(EquipmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class EquipmentDetailResponse(EquipmentResponse):
    active_project_id: Optional[UUID] = None
    active_project_name: Optional[str] = None
    total_operating_hours: Decimal = Decimal(0)
    total_fuel_cost: Decimal = Decimal(0)
    total_maintenance_cost: Decimal = Decimal(0)

class EquipmentSummaryResponse(BaseModel):
    total_units: int
    available_units: int
    in_use_units: int
    maintenance_units: int
    retired_units: int
    utilization_rate: Decimal
    total_operating_hours: Decimal
    total_fuel_cost: Decimal
    total_maintenance_cost: Decimal
    total_equipment_cost: Decimal

# -----------------------------------------------------------------------------
# Equipment Assignment
# -----------------------------------------------------------------------------
class EquipmentAssignmentBase(BaseModel):
    equipment_id: UUID
    project_id: UUID
    start_date: date
    end_date: Optional[date] = None
    hourly_cost_override: Optional[Decimal] = None

class EquipmentAssignmentCreate(EquipmentAssignmentBase):
    pass

class EquipmentAssignmentResponse(EquipmentAssignmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class EquipmentAssignmentDetailResponse(EquipmentAssignmentResponse):
    equipment_name: Optional[str] = None
    equipment_internal_id: Optional[str] = None
    project_name: Optional[str] = None

# -----------------------------------------------------------------------------
# Equipment Usage Log
# -----------------------------------------------------------------------------
class EquipmentUsageLineBase(BaseModel):
    project_id: UUID
    cost_code_id: UUID
    date: date
    hours: Decimal

class EquipmentUsageLineCreate(EquipmentUsageLineBase):
    pass

class EquipmentUsageLineResponse(EquipmentUsageLineBase):
    id: UUID
    usage_log_id: UUID
    hourly_cost_rate: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)

class EquipmentUsageLineDetailResponse(EquipmentUsageLineResponse):
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None
    cost_code_name: Optional[str] = None

class EquipmentUsageLogBase(BaseModel):
    equipment_id: UUID
    period_start: date
    period_end: date

class EquipmentUsageLogCreate(EquipmentUsageLogBase):
    lines: List[EquipmentUsageLineCreate]

class EquipmentUsageLogResponse(EquipmentUsageLogBase):
    id: UUID
    status: UsageLogStatus
    lines: List[EquipmentUsageLineResponse]
    model_config = ConfigDict(from_attributes=True)

class EquipmentUsageLogDetailResponse(BaseModel):
    id: UUID
    equipment_id: UUID
    equipment_name: Optional[str] = None
    equipment_internal_id: Optional[str] = None
    period_start: date
    period_end: date
    status: UsageLogStatus
    total_hours: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    lines: List[EquipmentUsageLineDetailResponse] = []
    model_config = ConfigDict(from_attributes=True)

# -----------------------------------------------------------------------------
# Fuel Transaction
# -----------------------------------------------------------------------------
class FuelTransactionBase(BaseModel):
    equipment_id: UUID
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    date: date
    volume: Decimal
    unit_cost: Decimal

class FuelTransactionCreate(FuelTransactionBase):
    pass

class FuelTransactionResponse(FuelTransactionBase):
    id: UUID
    total_cost: Decimal
    model_config = ConfigDict(from_attributes=True)

class FuelTransactionDetailResponse(FuelTransactionResponse):
    equipment_name: Optional[str] = None
    equipment_internal_id: Optional[str] = None
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None

# -----------------------------------------------------------------------------
# Maintenance Record
# -----------------------------------------------------------------------------
class MaintenanceRecordBase(BaseModel):
    equipment_id: UUID
    project_id: Optional[UUID] = None
    cost_code_id: Optional[UUID] = None
    type: MaintenanceType
    date: date
    description: str
    duration_hours: Optional[Decimal] = None
    cost: Decimal = Decimal(0)

class MaintenanceRecordCreate(MaintenanceRecordBase):
    pass

class MaintenanceRecordResponse(MaintenanceRecordBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class MaintenanceRecordDetailResponse(MaintenanceRecordResponse):
    equipment_name: Optional[str] = None
    equipment_internal_id: Optional[str] = None
    project_name: Optional[str] = None
    cost_code_code: Optional[str] = None
