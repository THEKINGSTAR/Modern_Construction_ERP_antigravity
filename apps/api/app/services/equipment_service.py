from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import List, Optional

from app.models.equipment import (
    Equipment, EquipmentAssignment, EquipmentUsageLog, EquipmentUsageLine,
    FuelTransaction, MaintenanceRecord, EquipmentStatus, UsageLogStatus
)
from app.models.projects import Project
from app.models.cost_codes import CostCode
from app.schemas.equipment import (
    EquipmentSummaryResponse, EquipmentDetailResponse, EquipmentUpdate,
    EquipmentAssignmentDetailResponse, EquipmentUsageLogDetailResponse,
    EquipmentUsageLineDetailResponse, FuelTransactionDetailResponse,
    MaintenanceRecordDetailResponse
)
from app.core.exceptions import BaseAPIException

class EquipmentService:
    def __init__(self, db: Session, tenant_id: UUID, user_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    def get_fleet_summary(self) -> EquipmentSummaryResponse:
        equipment_list = self.db.query(Equipment).filter(
            Equipment.tenant_id == self.tenant_id
        ).all()

        total_units = len(equipment_list)
        available_units = sum(1 for e in equipment_list if e.status == EquipmentStatus.AVAILABLE)
        in_use_units = sum(1 for e in equipment_list if e.status == EquipmentStatus.IN_USE)
        maintenance_units = sum(1 for e in equipment_list if e.status == EquipmentStatus.MAINTENANCE)
        retired_units = sum(1 for e in equipment_list if e.status == EquipmentStatus.RETIRED)

        active_base = available_units + in_use_units
        utilization_rate = Decimal(0)
        if active_base > 0:
            utilization_rate = (Decimal(in_use_units) / Decimal(active_base)) * Decimal(100)

        # Total operating hours & total usage cost
        usage_agg = self.db.query(
            func.coalesce(func.sum(EquipmentUsageLine.hours), 0),
            func.coalesce(func.sum(EquipmentUsageLine.total_cost), 0)
        ).join(
            EquipmentUsageLog, EquipmentUsageLine.usage_log_id == EquipmentUsageLog.id
        ).filter(
            EquipmentUsageLine.tenant_id == self.tenant_id,
            EquipmentUsageLog.status == UsageLogStatus.APPROVED
        ).first()
        total_hours = Decimal(str(usage_agg[0] if usage_agg else 0))
        total_usage_cost = Decimal(str(usage_agg[1] if usage_agg else 0))

        # Total fuel cost
        fuel_agg = self.db.query(
            func.coalesce(func.sum(FuelTransaction.total_cost), 0)
        ).filter(
            FuelTransaction.tenant_id == self.tenant_id
        ).scalar()
        total_fuel_cost = Decimal(str(fuel_agg or 0))

        # Total maintenance cost
        maint_agg = self.db.query(
            func.coalesce(func.sum(MaintenanceRecord.cost), 0)
        ).filter(
            MaintenanceRecord.tenant_id == self.tenant_id
        ).scalar()
        total_maintenance_cost = Decimal(str(maint_agg or 0))

        total_equipment_cost = total_usage_cost + total_fuel_cost + total_maintenance_cost

        return EquipmentSummaryResponse(
            total_units=total_units,
            available_units=available_units,
            in_use_units=in_use_units,
            maintenance_units=maintenance_units,
            retired_units=retired_units,
            utilization_rate=round(utilization_rate, 2),
            total_operating_hours=round(total_hours, 2),
            total_fuel_cost=round(total_fuel_cost, 2),
            total_maintenance_cost=round(total_maintenance_cost, 2),
            total_equipment_cost=round(total_equipment_cost, 2)
        )

    def list_equipment_with_details(self) -> List[EquipmentDetailResponse]:
        equipment_list = self.db.query(Equipment).filter(
            Equipment.tenant_id == self.tenant_id
        ).order_by(Equipment.internal_id.asc(), Equipment.name.asc()).all()

        today = date.today()
        result = []
        for eq in equipment_list:
            # Active assignment
            active_assign = self.db.query(EquipmentAssignment).filter(
                EquipmentAssignment.equipment_id == eq.id,
                EquipmentAssignment.tenant_id == self.tenant_id,
                EquipmentAssignment.start_date <= today,
                (EquipmentAssignment.end_date.is_(None) | (EquipmentAssignment.end_date >= today))
            ).order_by(EquipmentAssignment.start_date.desc()).first()

            active_proj_id = active_assign.project_id if active_assign else None
            active_proj_name = None
            if active_assign and active_assign.project:
                active_proj_name = active_assign.project.name

            # Aggregated hours
            hrs_agg = self.db.query(
                func.coalesce(func.sum(EquipmentUsageLine.hours), 0)
            ).join(
                EquipmentUsageLog, EquipmentUsageLine.usage_log_id == EquipmentUsageLog.id
            ).filter(
                EquipmentUsageLog.equipment_id == eq.id,
                EquipmentUsageLine.tenant_id == self.tenant_id,
                EquipmentUsageLog.status == UsageLogStatus.APPROVED
            ).scalar()
            tot_hours = Decimal(str(hrs_agg or 0))

            # Aggregated fuel
            fuel_agg = self.db.query(
                func.coalesce(func.sum(FuelTransaction.total_cost), 0)
            ).filter(
                FuelTransaction.equipment_id == eq.id,
                FuelTransaction.tenant_id == self.tenant_id
            ).scalar()
            tot_fuel = Decimal(str(fuel_agg or 0))

            # Aggregated maintenance
            maint_agg = self.db.query(
                func.coalesce(func.sum(MaintenanceRecord.cost), 0)
            ).filter(
                MaintenanceRecord.equipment_id == eq.id,
                MaintenanceRecord.tenant_id == self.tenant_id
            ).scalar()
            tot_maint = Decimal(str(maint_agg or 0))

            result.append(EquipmentDetailResponse(
                id=eq.id,
                name=eq.name,
                make=eq.make,
                model=eq.model,
                year=eq.year,
                serial_number=eq.serial_number,
                internal_id=eq.internal_id,
                status=eq.status,
                base_hourly_cost=eq.base_hourly_cost,
                active_project_id=active_proj_id,
                active_project_name=active_proj_name,
                total_operating_hours=round(tot_hours, 2),
                total_fuel_cost=round(tot_fuel, 2),
                total_maintenance_cost=round(tot_maint, 2)
            ))

        return result

    def update_equipment(self, equipment_id: UUID, data: EquipmentUpdate) -> Equipment:
        eq = self.db.query(Equipment).filter(
            Equipment.id == equipment_id,
            Equipment.tenant_id == self.tenant_id
        ).first()
        if not eq:
            raise BaseAPIException("Equipment not found", 404)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(eq, field, value)

        self.db.commit()
        self.db.refresh(eq)
        return eq

    def list_assignments(self) -> List[EquipmentAssignmentDetailResponse]:
        assignments = self.db.query(EquipmentAssignment).filter(
            EquipmentAssignment.tenant_id == self.tenant_id
        ).order_by(EquipmentAssignment.start_date.desc()).all()

        results = []
        for a in assignments:
            results.append(EquipmentAssignmentDetailResponse(
                id=a.id,
                equipment_id=a.equipment_id,
                project_id=a.project_id,
                start_date=a.start_date,
                end_date=a.end_date,
                hourly_cost_override=a.hourly_cost_override,
                equipment_name=a.equipment.name if a.equipment else None,
                equipment_internal_id=a.equipment.internal_id if a.equipment else None,
                project_name=a.project.name if a.project else None
            ))
        return results

    def list_usage_logs(self) -> List[EquipmentUsageLogDetailResponse]:
        logs = self.db.query(EquipmentUsageLog).filter(
            EquipmentUsageLog.tenant_id == self.tenant_id
        ).order_by(EquipmentUsageLog.period_start.desc()).all()

        results = []
        for log in logs:
            tot_hours = Decimal(0)
            tot_cost = Decimal(0)
            line_details = []
            for l in log.lines:
                tot_hours += l.hours or Decimal(0)
                tot_cost += l.total_cost or Decimal(0)
                line_details.append(EquipmentUsageLineDetailResponse(
                    id=l.id,
                    usage_log_id=l.usage_log_id,
                    project_id=l.project_id,
                    cost_code_id=l.cost_code_id,
                    date=l.date,
                    hours=l.hours,
                    hourly_cost_rate=l.hourly_cost_rate,
                    total_cost=l.total_cost,
                    project_name=l.project.name if l.project else None,
                    cost_code_code=l.cost_code.code if l.cost_code else None,
                    cost_code_name=l.cost_code.name if l.cost_code else None
                ))
            results.append(EquipmentUsageLogDetailResponse(
                id=log.id,
                equipment_id=log.equipment_id,
                equipment_name=log.equipment.name if log.equipment else None,
                equipment_internal_id=log.equipment.internal_id if log.equipment else None,
                period_start=log.period_start,
                period_end=log.period_end,
                status=log.status,
                total_hours=round(tot_hours, 2),
                total_cost=round(tot_cost, 2),
                lines=line_details
            ))
        return results

    def list_fuel_transactions(self) -> List[FuelTransactionDetailResponse]:
        txns = self.db.query(FuelTransaction).filter(
            FuelTransaction.tenant_id == self.tenant_id
        ).order_by(FuelTransaction.date.desc()).all()

        results = []
        for t in txns:
            results.append(FuelTransactionDetailResponse(
                id=t.id,
                equipment_id=t.equipment_id,
                project_id=t.project_id,
                cost_code_id=t.cost_code_id,
                date=t.date,
                volume=t.volume,
                unit_cost=t.unit_cost,
                total_cost=t.total_cost,
                equipment_name=t.equipment.name if t.equipment else None,
                equipment_internal_id=t.equipment.internal_id if t.equipment else None,
                project_name=t.project.name if t.project else None,
                cost_code_code=t.cost_code.code if t.cost_code else None
            ))
        return results

    def list_maintenance_records(self) -> List[MaintenanceRecordDetailResponse]:
        records = self.db.query(MaintenanceRecord).filter(
            MaintenanceRecord.tenant_id == self.tenant_id
        ).order_by(MaintenanceRecord.date.desc()).all()

        results = []
        for m in records:
            results.append(MaintenanceRecordDetailResponse(
                id=m.id,
                equipment_id=m.equipment_id,
                project_id=m.project_id,
                cost_code_id=m.cost_code_id,
                type=m.type,
                date=m.date,
                description=m.description,
                duration_hours=m.duration_hours,
                cost=m.cost,
                equipment_name=m.equipment.name if m.equipment else None,
                equipment_internal_id=m.equipment.internal_id if m.equipment else None,
                project_name=m.project.name if m.project else None,
                cost_code_code=m.cost_code.code if m.cost_code else None
            ))
        return results

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
