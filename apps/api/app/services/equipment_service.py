from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.models.equipment import (
    Equipment, EquipmentAssignment, EquipmentUsageLog, EquipmentUsageLine,
    UsageLogStatus
)
from app.core.exceptions import BaseAPIException

class EquipmentService:
    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def submit_usage_log(self, usage_log_id: UUID) -> EquipmentUsageLog:
        usage_log = self.db.query(EquipmentUsageLog).filter(
            EquipmentUsageLog.tenant_id == self.tenant_id,
            EquipmentUsageLog.id == usage_log_id
        ).first()

        if not usage_log:
            raise BaseAPIException("Usage log not found", 404)
        if usage_log.status != UsageLogStatus.DRAFT:
            raise BaseAPIException(f"Cannot submit usage log in {usage_log.status} status", 400)

        usage_log.status = UsageLogStatus.SUBMITTED
        self.db.commit()
        self.db.refresh(usage_log)
        return usage_log

    def approve_usage_log(self, usage_log_id: UUID) -> EquipmentUsageLog:
        usage_log = self.db.query(EquipmentUsageLog).filter(
            EquipmentUsageLog.tenant_id == self.tenant_id,
            EquipmentUsageLog.id == usage_log_id
        ).first()

        if not usage_log:
            raise BaseAPIException("Usage log not found", 404)
        if usage_log.status != UsageLogStatus.SUBMITTED:
            raise BaseAPIException(f"Cannot approve usage log in {usage_log.status} status", 400)

        equipment = self.db.query(Equipment).filter(
            Equipment.id == usage_log.equipment_id,
            Equipment.tenant_id == self.tenant_id
        ).first()

        for line in usage_log.lines:
            rate = self._get_applicable_rate(usage_log.equipment_id, line.project_id, line.date, equipment.base_hourly_cost)
            line.hourly_cost_rate = rate
            line.total_cost = line.hours * rate

        usage_log.status = UsageLogStatus.APPROVED
        self.db.commit()
        self.db.refresh(usage_log)
        return usage_log

    def _get_applicable_rate(self, equipment_id: UUID, project_id: UUID, current_date: date, fallback_rate: Decimal) -> Decimal:
        assignment = self.db.query(EquipmentAssignment).filter(
            EquipmentAssignment.equipment_id == equipment_id,
            EquipmentAssignment.project_id == project_id,
            EquipmentAssignment.start_date <= current_date,
            EquipmentAssignment.tenant_id == self.tenant_id
        ).order_by(EquipmentAssignment.start_date.desc()).first()
        
        if assignment and assignment.hourly_cost_override is not None:
            return assignment.hourly_cost_override
        
        return fallback_rate
