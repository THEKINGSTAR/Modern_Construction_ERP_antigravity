from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.equipment import (
    Equipment, EquipmentAssignment, EquipmentUsageLog, EquipmentUsageLine,
    FuelTransaction, MaintenanceRecord, UsageLogStatus
)
from app.schemas.equipment import (
    EquipmentCreate, EquipmentResponse,
    EquipmentAssignmentCreate, EquipmentAssignmentResponse,
    EquipmentUsageLogCreate, EquipmentUsageLogResponse,
    FuelTransactionCreate, FuelTransactionResponse,
    MaintenanceRecordCreate, MaintenanceRecordResponse
)
from app.services.equipment_service import EquipmentService

router = APIRouter()

# -----------------------------------------------------------------------------
# Equipment
# -----------------------------------------------------------------------------
@router.post("/", response_model=EquipmentResponse, status_code=201)
def create_equipment(
    data: EquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    eq = Equipment(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq

@router.get("/", response_model=List[EquipmentResponse])
def get_equipment_list(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Equipment).filter(Equipment.tenant_id == current_user.tenant_id).all()

# -----------------------------------------------------------------------------
# Equipment Assignments
# -----------------------------------------------------------------------------
@router.post("/assignments", response_model=EquipmentAssignmentResponse, status_code=201)
def create_assignment(
    data: EquipmentAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assignment = EquipmentAssignment(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

@router.get("/assignments", response_model=List[EquipmentAssignmentResponse])
def get_assignments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(EquipmentAssignment).filter(EquipmentAssignment.tenant_id == current_user.tenant_id).all()

# -----------------------------------------------------------------------------
# Equipment Usage Logs
# -----------------------------------------------------------------------------
@router.post("/usage-logs", response_model=EquipmentUsageLogResponse, status_code=201)
def create_usage_log(
    data: EquipmentUsageLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log_data = data.model_dump(exclude={"lines"})
    usage_log = EquipmentUsageLog(**log_data, tenant_id=current_user.tenant_id)
    db.add(usage_log)
    db.flush()

    for line_data in data.lines:
        line = EquipmentUsageLine(**line_data.model_dump(), usage_log_id=usage_log.id, tenant_id=current_user.tenant_id)
        db.add(line)

    db.commit()
    db.refresh(usage_log)
    return usage_log

@router.get("/usage-logs/{log_id}", response_model=EquipmentUsageLogResponse)
def get_usage_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = db.query(EquipmentUsageLog).filter(
        EquipmentUsageLog.tenant_id == current_user.tenant_id,
        EquipmentUsageLog.id == log_id
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Usage log not found")
    return log

@router.post("/usage-logs/{log_id}/submit", response_model=EquipmentUsageLogResponse)
def submit_usage_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = EquipmentService(db, current_user.tenant_id, current_user.id)
    return service.submit_usage_log(log_id)

@router.post("/usage-logs/{log_id}/approve", response_model=EquipmentUsageLogResponse)
def approve_usage_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = EquipmentService(db, current_user.tenant_id, current_user.id)
    return service.approve_usage_log(log_id)

# -----------------------------------------------------------------------------
# Fuel Transactions
# -----------------------------------------------------------------------------
@router.post("/fuel", response_model=FuelTransactionResponse, status_code=201)
def create_fuel_transaction(
    data: FuelTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_cost = data.volume * data.unit_cost
    txn = FuelTransaction(**data.model_dump(), total_cost=total_cost, tenant_id=current_user.tenant_id)
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn

# -----------------------------------------------------------------------------
# Maintenance Records
# -----------------------------------------------------------------------------
@router.post("/maintenance", response_model=MaintenanceRecordResponse, status_code=201)
def create_maintenance_record(
    data: MaintenanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = MaintenanceRecord(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
