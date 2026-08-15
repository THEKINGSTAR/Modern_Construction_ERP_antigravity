from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, null
from typing import List, Dict
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from collections import defaultdict

from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from app.models.budgets import Budget, BudgetLine
from app.models.forecasts import ProjectForecast, ProjectForecastLine, ForecastStatus
from app.models.hr import Timesheet, TimesheetLine, TimesheetStatus

class CostTransaction(BaseModel):
    project_id: UUID
    cost_code_id: UUID
    date: date
    amount: Decimal
    currency: str
    source_type: str
    source_id: UUID
    cost_type: str

class CostCodeSummary(BaseModel):
    cost_code_id: UUID
    original_budget: Decimal = Decimal(0)
    approved_changes: Decimal = Decimal(0)
    current_budget: Decimal = Decimal(0)
    committed_cost: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    estimate_to_complete: Decimal = Decimal(0)
    estimate_at_completion: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)

class ProjectCostEngine:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def get_cost_transactions(self, project_id: UUID) -> List[CostTransaction]:
        transactions = []
        
        # 1. COMMITTED COSTS from Purchase Orders
        # A PO is committed if it is not DRAFT and not CANCELLED
        po_query = (
            select(
                PurchaseOrder.project_id,
                PurchaseOrderLine.cost_code_id,
                PurchaseOrder.issue_date,
                PurchaseOrderLine.amount,
                PurchaseOrder.currency,
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
            # issue_date can be None if not fully issued, fallback to today or mock
            txn_date = row.issue_date or date.today()
            transactions.append(
                CostTransaction(
                    project_id=row.project_id,
                    cost_code_id=row.cost_code_id,
                    date=txn_date,
                    amount=row.amount,
                    currency=row.currency or "BASE",
                    source_type="PURCHASE_ORDER",
                    source_id=row.source_id,
                    cost_type="COMMITTED"
                )
            )

        # 2. ACTUAL COSTS from Material Issues
        # Material issues are actual costs when POSTED
        mi_query = (
            select(
                MaterialIssue.project_id,
                MaterialIssue.cost_code_id,
                MaterialIssue.date,
                (MaterialIssueLine.quantity * MaterialIssueLine.unit_cost).label("amount"),
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
            transactions.append(
                CostTransaction(
                    project_id=row.project_id,
                    cost_code_id=row.cost_code_id,
                    date=row.date,
                    amount=row.amount,
                    currency="BASE", # Material issues use base inventory currency
                    source_type="MATERIAL_ISSUE",
                    source_id=row.source_id,
                    cost_type="ACTUAL"
                )
            )

        # 3. ACTUAL COSTS from Labor (Timesheets)
        # Timesheets are actual costs when APPROVED
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
            if row.amount:
                transactions.append(
                    CostTransaction(
                        project_id=row.project_id,
                        cost_code_id=row.cost_code_id,
                        date=row.date,
                        amount=row.amount,
                        currency="BASE",
                        source_type="TIMESHEET",
                        source_id=row.source_id,
                        cost_type="ACTUAL"
                    )
                )

        return sorted(transactions, key=lambda x: x.date)

    def get_project_cost_summary(self, project_id: UUID) -> List[CostCodeSummary]:
        summaries: Dict[UUID, CostCodeSummary] = {}
        
        # Helper to get or create summary
        def get_summary(cc_id: UUID) -> CostCodeSummary:
            if cc_id not in summaries:
                summaries[cc_id] = CostCodeSummary(cost_code_id=cc_id)
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
            summary.original_budget += row.original_budget
            summary.approved_changes += row.approved_changes
            summary.current_budget = summary.original_budget + summary.approved_changes

        # 2. Load Costs
        transactions = self.get_cost_transactions(project_id)
        for txn in transactions:
            summary = get_summary(txn.cost_code_id)
            if txn.cost_type == "COMMITTED":
                summary.committed_cost += txn.amount
            elif txn.cost_type == "ACTUAL":
                summary.actual_cost += txn.amount

        # 3. Load Forecasts (ETC)
        # Find latest APPROVED forecast
        latest_forecast = (
            select(ProjectForecast.id)
            .where(
                ProjectForecast.tenant_id == self.tenant_id,
                ProjectForecast.project_id == project_id,
                ProjectForecast.status == ForecastStatus.APPROVED
            )
            .order_by(ProjectForecast.date.desc(), ProjectForecast.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        
        forecast_query = (
            select(ProjectForecastLine.cost_code_id, ProjectForecastLine.etc_amount)
            .where(ProjectForecastLine.forecast_id == latest_forecast)
        )
        
        for row in self.db.execute(forecast_query):
            summary = get_summary(row.cost_code_id)
            summary.estimate_to_complete = row.etc_amount

        # 4. Calculate EAC and Variance
        for summary in summaries.values():
            # If ETC is explicitly 0 and no forecast exists, what is EAC?
            # Standard logic: EAC = Actual + ETC. If ETC is provided, use it. 
            # If not, naive EAC might equal Current Budget or Actual Cost. 
            # We strictly use: EAC = Actual Cost + ETC.
            summary.estimate_at_completion = summary.actual_cost + summary.estimate_to_complete
            summary.variance = summary.current_budget - summary.estimate_at_completion

        return list(summaries.values())
