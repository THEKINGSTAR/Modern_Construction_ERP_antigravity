from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, or_
from typing import List, Dict, Optional
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from collections import defaultdict
from fastapi import HTTPException

from app.models.projects import Project
from app.models.contracts import Contract
from app.models.cost_codes import CostCode, CostCategory
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from app.models.budgets import Budget, BudgetLine
from app.models.forecasts import ProjectForecast, ProjectForecastLine, ForecastStatus
from app.models.hr import Timesheet, TimesheetLine, TimesheetStatus
from app.models.commercial import Subcontract, ClientPaymentApplication, PaymentAppStatus
from app.models.ap_ar import APInvoice, APInvoiceLine, InvoiceStatus
from app.models.accounting import Journal, JournalLine, JournalStatus, Account, AccountType
from app.models.equipment import (
    EquipmentUsageLog, EquipmentUsageLine, UsageLogStatus,
    FuelTransaction, MaintenanceRecord
)
from app.schemas.project_cost import (
    CostTransactionResponse,
    CostCodeSummaryResponse,
    ProjectCostKPISummary,
    PortfolioCostSummaryResponse
)

class CostTransaction(BaseModel):
    project_id: UUID
    cost_code_id: Optional[UUID] = None
    cost_code_code: Optional[str] = None
    cost_code_name: Optional[str] = None
    date: date
    amount: Decimal
    currency: str
    source_type: str
    source_id: UUID
    source_reference: Optional[str] = None
    cost_type: str

class CostCodeSummary(BaseModel):
    cost_code_id: UUID
    cost_code_code: Optional[str] = None
    cost_code_name: Optional[str] = None
    cost_category: Optional[str] = None
    original_budget: Decimal = Decimal("0.0")
    approved_changes: Decimal = Decimal("0.0")
    current_budget: Decimal = Decimal("0.0")
    committed_cost: Decimal = Decimal("0.0")
    actual_cost: Decimal = Decimal("0.0")
    estimate_to_complete: Decimal = Decimal("0.0")
    estimate_at_completion: Decimal = Decimal("0.0")
    variance: Decimal = Decimal("0.0")
    variance_percentage: Decimal = Decimal("0.0")
    status: str = "ON_TRACK"

class ProjectCostEngine:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _get_cost_code_map(self) -> Dict[UUID, CostCode]:
        codes = self.db.query(CostCode).filter(CostCode.tenant_id == self.tenant_id).all()
        return {c.id: c for c in codes}

    def get_cost_transactions(self, project_id: UUID) -> List[CostTransaction]:
        transactions: List[CostTransaction] = []
        cc_map = self._get_cost_code_map()

        # 1. COMMITTED COSTS from Purchase Orders
        po_query = (
            select(
                PurchaseOrder.project_id,
                PurchaseOrderLine.cost_code_id,
                PurchaseOrder.issue_date,
                PurchaseOrderLine.amount,
                PurchaseOrder.currency,
                PurchaseOrder.po_number,
                PurchaseOrder.id.label("source_id")
            )
            .select_from(PurchaseOrder)
            .join(PurchaseOrderLine, PurchaseOrder.id == PurchaseOrderLine.purchase_order_id)
            .where(
                PurchaseOrder.tenant_id == self.tenant_id,
                PurchaseOrder.project_id == project_id,
                PurchaseOrder.status.not_in([POStatus.DRAFT, POStatus.CANCELLED]),
                PurchaseOrderLine.cost_code_id.is_not(None)
            )
        )
        
        for row in self.db.execute(po_query):
            txn_date = row.issue_date or date.today()
            cc = cc_map.get(row.cost_code_id)
            transactions.append(
                CostTransaction(
                    project_id=row.project_id,
                    cost_code_id=row.cost_code_id,
                    cost_code_code=cc.code if cc else None,
                    cost_code_name=cc.name if cc else None,
                    date=txn_date,
                    amount=Decimal(str(row.amount)),
                    currency=row.currency or "USD",
                    source_type="PURCHASE_ORDER",
                    source_id=row.source_id,
                    source_reference=row.po_number,
                    cost_type="COMMITTED"
                )
            )

        # 2. COMMITTED COSTS from Trade Subcontracts
        sub_query = (
            select(
                Subcontract.id.label("source_id"),
                Subcontract.project_id,
                Subcontract.subcontract_number,
                Subcontract.current_value,
                Subcontract.start_date
            )
            .where(
                Subcontract.tenant_id == self.tenant_id,
                Subcontract.project_id == project_id
            )
        )
        
        # Find default subcontract cost code if exists
        sub_cc = next((c for c in cc_map.values() if c.category == CostCategory.SUBCONTRACT or "05-" in c.code or "Subcontract" in c.name), None)
        sub_cc_id = sub_cc.id if sub_cc else (list(cc_map.keys())[0] if cc_map else None)

        for row in self.db.execute(sub_query):
            if row.current_value and Decimal(str(row.current_value)) > 0 and sub_cc_id:
                txn_date = row.start_date or date.today()
                cc = cc_map.get(sub_cc_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=sub_cc_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=txn_date,
                        amount=Decimal(str(row.current_value)),
                        currency="USD",
                        source_type="SUBCONTRACT",
                        source_id=row.source_id,
                        source_reference=row.subcontract_number,
                        cost_type="COMMITTED"
                    )
                )

        # 3. ACTUAL COSTS from Material Issues
        mi_query = (
            select(
                MaterialIssue.project_id,
                MaterialIssue.cost_code_id,
                MaterialIssue.date,
                (MaterialIssueLine.quantity * MaterialIssueLine.unit_cost).label("amount"),
                MaterialIssue.issue_number,
                MaterialIssue.id.label("source_id")
            )
            .select_from(MaterialIssue)
            .join(MaterialIssueLine, MaterialIssue.id == MaterialIssueLine.material_issue_id)
            .where(
                MaterialIssue.tenant_id == self.tenant_id,
                MaterialIssue.project_id == project_id,
                MaterialIssue.status == MaterialIssueStatus.POSTED
            )
        )

        for row in self.db.execute(mi_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="MATERIAL_ISSUE",
                        source_id=row.source_id,
                        source_reference=row.issue_number,
                        cost_type="ACTUAL"
                    )
                )

        # 4. ACTUAL COSTS from AP Invoices (Posted or Paid)
        ap_query = (
            select(
                APInvoiceLine.project_id,
                APInvoiceLine.cost_code_id,
                APInvoice.date,
                APInvoiceLine.line_total.label("amount"),
                APInvoice.number.label("invoice_number"),
                APInvoice.id.label("source_id")
            )
            .select_from(APInvoice)
            .join(APInvoiceLine, APInvoice.id == APInvoiceLine.invoice_id)
            .where(
                APInvoice.tenant_id == self.tenant_id,
                APInvoiceLine.project_id == project_id,
                APInvoice.status.in_([InvoiceStatus.POSTED, InvoiceStatus.PAID]),
                APInvoiceLine.cost_code_id.is_not(None),
                APInvoiceLine.material_id.is_(None),
                APInvoiceLine.goods_receipt_line_id.is_(None)
            )
        )
        for row in self.db.execute(ap_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="AP_INVOICE",
                        source_id=row.source_id,
                        source_reference=row.invoice_number,
                        cost_type="ACTUAL"
                    )
                )

        # 5. ACTUAL COSTS from Labor (Timesheets)
        ts_query = (
            select(
                TimesheetLine.project_id,
                TimesheetLine.cost_code_id,
                TimesheetLine.date,
                TimesheetLine.total_cost.label("amount"),
                Timesheet.id.label("source_id")
            )
            .select_from(Timesheet)
            .join(TimesheetLine, Timesheet.id == TimesheetLine.timesheet_id)
            .where(
                Timesheet.tenant_id == self.tenant_id,
                TimesheetLine.project_id == project_id,
                Timesheet.status == TimesheetStatus.APPROVED
            )
        )

        for row in self.db.execute(ts_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="TIMESHEET",
                        source_id=row.source_id,
                        source_reference="Timesheet Log",
                        cost_type="ACTUAL"
                    )
                )

        # 6. ACTUAL COSTS from Equipment Usage
        eq_query = (
            select(
                EquipmentUsageLine.project_id,
                EquipmentUsageLine.cost_code_id,
                EquipmentUsageLine.date,
                EquipmentUsageLine.total_cost.label("amount"),
                EquipmentUsageLog.id.label("source_id")
            )
            .select_from(EquipmentUsageLog)
            .join(EquipmentUsageLine, EquipmentUsageLog.id == EquipmentUsageLine.usage_log_id)
            .where(
                EquipmentUsageLog.tenant_id == self.tenant_id,
                EquipmentUsageLine.project_id == project_id,
                EquipmentUsageLog.status == UsageLogStatus.APPROVED
            )
        )

        for row in self.db.execute(eq_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="EQUIPMENT_USAGE",
                        source_id=row.source_id,
                        source_reference="Equipment Log",
                        cost_type="ACTUAL"
                    )
                )

        # 7. ACTUAL COSTS from Equipment Fuel
        fuel_query = (
            select(
                FuelTransaction.project_id,
                FuelTransaction.cost_code_id,
                FuelTransaction.date,
                FuelTransaction.total_cost.label("amount"),
                FuelTransaction.id.label("source_id")
            )
            .select_from(FuelTransaction)
            .where(
                FuelTransaction.tenant_id == self.tenant_id,
                FuelTransaction.project_id == project_id
            )
        )

        for row in self.db.execute(fuel_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="EQUIPMENT_FUEL",
                        source_id=row.source_id,
                        source_reference="Fuel Log",
                        cost_type="ACTUAL"
                    )
                )

        # 8. ACTUAL COSTS from Equipment Maintenance
        maint_query = (
            select(
                MaintenanceRecord.project_id,
                MaintenanceRecord.cost_code_id,
                MaintenanceRecord.date,
                MaintenanceRecord.cost.label("amount"),
                MaintenanceRecord.id.label("source_id")
            )
            .select_from(MaintenanceRecord)
            .where(
                MaintenanceRecord.tenant_id == self.tenant_id,
                MaintenanceRecord.project_id == project_id
            )
        )

        for row in self.db.execute(maint_query):
            if row.amount and Decimal(str(row.amount)) > 0:
                cc = cc_map.get(row.cost_code_id)
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        cost_code_code=cc.code if cc else None,
                        cost_code_name=cc.name if cc else None,
                        date=row.date or date.today(),
                        amount=Decimal(str(row.amount)),
                        currency="USD",
                        source_type="EQUIPMENT_MAINTENANCE",
                        source_id=row.source_id,
                        source_reference="Maintenance Log",
                        cost_type="ACTUAL"
                    )
                )

        return sorted(transactions, key=lambda x: x.date)

    def get_project_cost_summary(self, project_id: UUID) -> List[CostCodeSummary]:
        summaries: Dict[UUID, CostCodeSummary] = {}
        cc_map = self._get_cost_code_map()
        
        def get_summary(cc_id: UUID) -> CostCodeSummary:
            if cc_id not in summaries:
                cc = cc_map.get(cc_id)
                summaries[cc_id] = CostCodeSummary(
                    cost_code_id=cc_id,
                    cost_code_code=cc.code if cc else None,
                    cost_code_name=cc.name if cc else None,
                    cost_category=str(cc.category.value if cc and cc.category else "GENERAL")
                )
            return summaries[cc_id]

        # 1. Load Budgets
        budget_query = (
            select(
                BudgetLine.cost_code_id,
                BudgetLine.original_budget,
                BudgetLine.approved_changes
            )
            .select_from(Budget)
            .join(BudgetLine, Budget.id == BudgetLine.budget_id)
            .where(
                Budget.tenant_id == self.tenant_id,
                Budget.project_id == project_id,
                Budget.status == "APPROVED"
            )
        )
        for row in self.db.execute(budget_query):
            summary = get_summary(row.cost_code_id)
            summary.original_budget += Decimal(str(row.original_budget or 0))
            summary.approved_changes += Decimal(str(row.approved_changes or 0))
            summary.current_budget = summary.original_budget + summary.approved_changes

        # 2. Load Costs
        transactions = self.get_cost_transactions(project_id)
        for txn in transactions:
            if txn.cost_code_id:
                summary = get_summary(txn.cost_code_id)
                if txn.cost_type == "COMMITTED":
                    summary.committed_cost += txn.amount
                elif txn.cost_type == "ACTUAL":
                    summary.actual_cost += txn.amount

        # 3. Load Forecasts (ETC)
        latest_forecast = (
            select(ProjectForecast.id)
            .where(
                ProjectForecast.tenant_id == self.tenant_id,
                ProjectForecast.project_id == project_id,
                ProjectForecast.status == ForecastStatus.APPROVED
            )
            .order_by(ProjectForecast.created_at.desc(), ProjectForecast.date.desc())
            .limit(1)
            .scalar_subquery()
        )
        
        forecast_query = (
            select(ProjectForecastLine.cost_code_id, ProjectForecastLine.etc_amount)
            .where(ProjectForecastLine.forecast_id == latest_forecast)
        )
        
        for row in self.db.execute(forecast_query):
            summary = get_summary(row.cost_code_id)
            summary.estimate_to_complete = Decimal(str(row.etc_amount or 0))

        # 4. Calculate EAC, Variance & Status
        for summary in summaries.values():
            summary.estimate_at_completion = summary.actual_cost + summary.estimate_to_complete
            summary.variance = summary.current_budget - summary.estimate_at_completion
            if summary.current_budget > 0:
                summary.variance_percentage = ((summary.variance / summary.current_budget) * Decimal("100.0")).quantize(Decimal("0.1"))
            
            if summary.variance >= Decimal("0.0"):
                summary.status = "UNDER_BUDGET" if summary.variance > Decimal("0.0") else "ON_TRACK"
            else:
                pct = abs(summary.variance_percentage)
                summary.status = "AT_RISK" if pct <= Decimal("5.0") else "OVER_BUDGET"

        return sorted(list(summaries.values()), key=lambda x: x.cost_code_code or "")

    def get_project_kpi_summary(self, project_id: UUID) -> ProjectCostKPISummary:
        proj = self.db.query(Project).filter(Project.id == project_id, Project.tenant_id == self.tenant_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

        summaries = self.get_project_cost_summary(project_id)
        p_orig = sum((s.original_budget for s in summaries), Decimal("0.0"))
        p_chg = sum((s.approved_changes for s in summaries), Decimal("0.0"))
        p_cur = sum((s.current_budget for s in summaries), Decimal("0.0"))
        p_com = sum((s.committed_cost for s in summaries), Decimal("0.0"))
        p_act = sum((s.actual_cost for s in summaries), Decimal("0.0"))
        p_etc = sum((s.estimate_to_complete for s in summaries), Decimal("0.0"))
        p_eac = sum((s.estimate_at_completion for s in summaries), Decimal("0.0"))
        p_var = sum((s.variance for s in summaries), Decimal("0.0"))

        # EV: Earned Value certified work from client payment applications
        ev_sum = self.db.execute(
            select(func.coalesce(func.sum(ClientPaymentApplication.gross_work), Decimal("0.0")))
            .join(Contract, ClientPaymentApplication.contract_id == Contract.id)
            .where(
                ClientPaymentApplication.tenant_id == self.tenant_id,
                Contract.project_id == project_id,
                ClientPaymentApplication.status.in_([PaymentAppStatus.APPROVED, PaymentAppStatus.POSTED, PaymentAppStatus.PAID])
            )
        ).scalar() or Decimal("0.0")

        cpi = (Decimal(str(ev_sum)) / p_act).quantize(Decimal("0.01")) if p_act > 0 else Decimal("1.00")
        
        p_status = "ON_TRACK"
        if p_var > Decimal("0.0"):
            p_status = "UNDER_BUDGET"
        elif p_var < Decimal("0.0"):
            p_status = "OVER_BUDGET" if abs(p_var) > (p_cur * Decimal("0.05")) else "AT_RISK"

        return ProjectCostKPISummary(
            project_id=proj.id,
            project_name=proj.name,
            project_number=proj.project_number,
            total_original_budget=p_orig,
            total_approved_changes=p_chg,
            total_current_budget=p_cur,
            total_committed=p_com,
            total_actual=p_act,
            total_estimate_to_complete=p_etc,
            total_estimate_at_completion=p_eac,
            total_variance=p_var,
            cost_performance_index=cpi,
            status=p_status
        )

    def get_portfolio_cost_summary(self) -> PortfolioCostSummaryResponse:
        projects = self.db.query(Project).filter(Project.tenant_id == self.tenant_id).all()
        project_kpis: List[ProjectCostKPISummary] = []

        total_budget = Decimal("0.0")
        total_committed = Decimal("0.0")
        total_actual = Decimal("0.0")
        total_etc = Decimal("0.0")
        total_eac = Decimal("0.0")
        total_variance = Decimal("0.0")

        for proj in projects:
            kpi = self.get_project_kpi_summary(proj.id)
            project_kpis.append(kpi)

            total_budget += kpi.total_current_budget
            total_committed += kpi.total_committed
            total_actual += kpi.total_actual
            total_etc += kpi.total_estimate_to_complete
            total_eac += kpi.total_estimate_at_completion
            total_variance += kpi.total_variance

        overall_cpi = (sum(k.cost_performance_index for k in project_kpis) / len(project_kpis)).quantize(Decimal("0.01")) if project_kpis else Decimal("1.00")

        return PortfolioCostSummaryResponse(
            total_projects=len(projects),
            total_budget=total_budget,
            total_committed=total_committed,
            total_actual=total_actual,
            total_etc=total_etc,
            total_eac=total_eac,
            total_variance=total_variance,
            overall_cpi=overall_cpi,
            projects=project_kpis
        )
