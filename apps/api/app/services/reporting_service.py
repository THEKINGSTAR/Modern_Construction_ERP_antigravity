from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, or_, case
from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal

from app.schemas.reports import (
    ProjectDashboardMetrics, CostCodeDetail, BudgetVsActualReport,
    CommitmentReport, CommitmentDetail, AgingReport, AgingDetail, AgingBucket,
    TrialBalanceReport, TrialBalanceLine, ExecutiveDashboardReport
)
from app.services.project_cost import ProjectCostEngine
from app.models.contracts import Contract
from app.models.commercial import ClientChangeOrder, Subcontract, ClientPaymentApplication, PaymentAppStatus, SubcontractPaymentApplication
from app.models.ap_ar import APInvoice, ARInvoice, PaymentAllocation, Payment, InvoiceStatus, PaymentStatus, APInvoiceLine, ARInvoiceLine
from app.models.accounting import JournalLine, Account, Journal, JournalStatus
from app.models.cost_codes import CostCode
from app.models.projects import Project
from app.models.suppliers import Supplier
from app.models.clients import Client

class ReportingService:
    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        
    def get_project_dashboard(self, project_id: UUID) -> ProjectDashboardMetrics:
        # 1. Base cost metrics via ProjectCostEngine
        cost_engine = ProjectCostEngine(self.db, self.tenant_id)
        cost_summaries = cost_engine.get_project_cost_summary(project_id)
        
        metrics = ProjectDashboardMetrics(project_id=project_id)
        for cs in cost_summaries:
            metrics.original_budget += cs.original_budget
            metrics.current_budget += cs.current_budget
            metrics.committed_cost += cs.committed_cost
            metrics.actual_cost += cs.actual_cost
            metrics.forecast_cost += cs.estimate_to_complete
            metrics.estimate_at_completion += cs.estimate_at_completion
            metrics.variance += cs.variance
            
        # 2. Contract Value
        contracts_query = select(Contract).where(Contract.tenant_id == self.tenant_id, Contract.project_id == project_id)
        contracts = self.db.execute(contracts_query).scalars().all()
        for c in contracts:
            metrics.contract_value += c.original_value
            metrics.current_contract_value += c.current_value
            
        # 3. Billed (AR Invoices & Client Payment Applications)
        # Assuming Client Payment Apps directly update Contract or are the source of billing, 
        # but AR Invoices are the universal standard for "Billed".
        ar_inv_query = select(func.coalesce(func.sum(ARInvoice.total_amount), Decimal(0))).join(
            ClientPaymentApplication, ClientPaymentApplication.id == ARInvoice.id, isouter=True # Or direct link if any, but AR Invoice lines have project_id
        ).select_from(ARInvoice).where(
            ARInvoice.tenant_id == self.tenant_id,
            ARInvoice.status != InvoiceStatus.DRAFT,
            ARInvoice.status != InvoiceStatus.VOID,
            # To strictly filter by project, we might need ARInvoiceLine
            ARInvoice.id.in_(
                select(ARInvoiceLine.invoice_id)
                .where(ARInvoiceLine.project_id == project_id)
            )
        )
        metrics.billed = self.db.execute(ar_inv_query).scalar() or Decimal(0)
        
        # 4. Collected
        collected_query = select(func.coalesce(func.sum(PaymentAllocation.amount), Decimal(0))).join(
            ARInvoice, ARInvoice.id == PaymentAllocation.ar_invoice_id
        ).where(
            PaymentAllocation.tenant_id == self.tenant_id,
            ARInvoice.id.in_(
                select(ARInvoiceLine.invoice_id)
                .where(ARInvoiceLine.project_id == project_id)
            )
        )
        metrics.collected = self.db.execute(collected_query).scalar() or Decimal(0)
        metrics.receivable = metrics.billed - metrics.collected
        
        # 5. Payable
        # AP Invoices total
        ap_inv_query = select(func.coalesce(func.sum(APInvoice.total_amount), Decimal(0))).where(
            APInvoice.tenant_id == self.tenant_id,
            APInvoice.status != InvoiceStatus.DRAFT,
            APInvoice.status != InvoiceStatus.VOID,
            APInvoice.id.in_(
                select(APInvoiceLine.invoice_id)
                .where(APInvoiceLine.project_id == project_id)
            )
        )
        ap_billed = self.db.execute(ap_inv_query).scalar() or Decimal(0)
        
        ap_paid_query = select(func.coalesce(func.sum(PaymentAllocation.amount), Decimal(0))).join(
            APInvoice, APInvoice.id == PaymentAllocation.ap_invoice_id
        ).where(
            PaymentAllocation.tenant_id == self.tenant_id,
            APInvoice.id.in_(
                select(APInvoiceLine.invoice_id)
                .where(APInvoiceLine.project_id == project_id)
            )
        )
        ap_paid = self.db.execute(ap_paid_query).scalar() or Decimal(0)
        metrics.payable = ap_billed - ap_paid
        
        # 6. Profitability
        metrics.gross_profit = metrics.current_contract_value - metrics.estimate_at_completion
        if metrics.current_contract_value > 0:
            metrics.margin_percentage = (metrics.gross_profit / metrics.current_contract_value) * 100
            
        return metrics

    def get_budget_vs_actual(self, project_id: UUID) -> BudgetVsActualReport:
        project = self.db.execute(select(Project).where(Project.id == project_id)).scalar_one()
        cost_engine = ProjectCostEngine(self.db, self.tenant_id)
        cost_summaries = cost_engine.get_project_cost_summary(project_id)
        
        cost_code_ids = [cs.cost_code_id for cs in cost_summaries]
        cost_codes = self.db.execute(select(CostCode).where(CostCode.id.in_(cost_code_ids))).scalars().all()
        cc_map = {cc.id: cc.name for cc in cost_codes}
        
        report = BudgetVsActualReport(project_id=project.id, project_name=project.name)
        for cs in cost_summaries:
            detail = CostCodeDetail(
                cost_code_id=cs.cost_code_id,
                cost_code_name=cc_map.get(cs.cost_code_id, "Unknown"),
                original_budget=cs.original_budget,
                current_budget=cs.current_budget,
                actual_cost=cs.actual_cost,
                variance=cs.current_budget - cs.actual_cost
            )
            report.details.append(detail)
            report.total_budget += detail.current_budget
            report.total_actual += detail.actual_cost
            report.total_variance += detail.variance
            
        return report

    def get_ap_aging(self, as_of_date: date) -> AgingReport:
        # Calculate days outstanding
        # DRAFT/VOID invoices are excluded
        query = select(
            Supplier.id.label("party_id"),
            Supplier.name.label("party_name"),
            APInvoice.id.label("invoice_id"),
            APInvoice.total_amount,
            APInvoice.due_date,
            func.coalesce(
                select(func.sum(PaymentAllocation.amount))
                .where(PaymentAllocation.ap_invoice_id == APInvoice.id)
                .correlate(APInvoice)
                .scalar_subquery(), 
                Decimal(0)
            ).label("paid_amount")
        ).join(Supplier, Supplier.id == APInvoice.supplier_id).where(
            APInvoice.tenant_id == self.tenant_id,
            APInvoice.date <= as_of_date,
            APInvoice.status.not_in([InvoiceStatus.DRAFT, InvoiceStatus.VOID])
        )
        
        totals = AgingBucket()
        details_map = {}
        
        for row in self.db.execute(query):
            outstanding = row.total_amount - row.paid_amount
            if outstanding <= 0:
                continue
                
            if row.party_id not in details_map:
                details_map[row.party_id] = AgingDetail(
                    party_id=row.party_id,
                    party_name=row.party_name,
                    buckets=AgingBucket()
                )
                
            b = details_map[row.party_id].buckets
            days_past_due = (as_of_date - row.due_date).days
            
            if days_past_due <= 0:
                b.current += outstanding
                totals.current += outstanding
            elif days_past_due <= 30:
                b.days_1_30 += outstanding
                totals.days_1_30 += outstanding
            elif days_past_due <= 60:
                b.days_31_60 += outstanding
                totals.days_31_60 += outstanding
            elif days_past_due <= 90:
                b.days_61_90 += outstanding
                totals.days_61_90 += outstanding
            else:
                b.over_90 += outstanding
                totals.over_90 += outstanding
                
            b.total += outstanding
            totals.total += outstanding
            
        return AgingReport(
            as_of_date=as_of_date,
            type="AP",
            details=list(details_map.values()),
            totals=totals
        )

    def get_trial_balance(self, as_of_date: date) -> TrialBalanceReport:
        query = select(
            Account.id,
            Account.account_code,
            Account.name,
            func.coalesce(func.sum(JournalLine.debit), Decimal(0)).label("debit"),
            func.coalesce(func.sum(JournalLine.credit), Decimal(0)).label("credit")
        ).join(
            JournalLine, JournalLine.account_id == Account.id, isouter=True
        ).join(
            Journal, Journal.id == JournalLine.journal_id, isouter=True
        ).where(
            Account.tenant_id == self.tenant_id,
            or_(Journal.date <= as_of_date, Journal.date == None),
            or_(Journal.status == JournalStatus.POSTED, Journal.status == None)
        ).group_by(Account.id, Account.account_code, Account.name)
        
        report = TrialBalanceReport(as_of_date=as_of_date)
        for row in self.db.execute(query):
            net_debit = row.debit - row.credit
            if net_debit > 0:
                d = net_debit
                c = Decimal(0)
            elif net_debit < 0:
                d = Decimal(0)
                c = abs(net_debit)
            else:
                d = Decimal(0)
                c = Decimal(0)
                
            if d > 0 or c > 0:
                report.lines.append(TrialBalanceLine(
                    account_id=row.id,
                    account_code=row.account_code,
                    account_name=row.name,
                    debit=d,
                    credit=c
                ))
                report.total_debit += d
                report.total_credit += c
                
        return report

    def get_executive_dashboard(self) -> ExecutiveDashboardReport:
        from app.models.inventory import InventoryBalance
        from app.models.warehouses import Warehouse
        from app.models.contracts import ContractStatus

        contracts_q = select(
            func.count(Contract.id),
            func.coalesce(func.sum(Contract.current_value), Decimal(0))
        ).where(Contract.tenant_id == self.tenant_id, Contract.status != ContractStatus.CANCELLED)
        active_contracts, contract_val = self.db.execute(contracts_q).one()

        projects_total_q = select(func.count(Project.id)).where(Project.tenant_id == self.tenant_id)
        total_projects = self.db.execute(projects_total_q).scalar_one()

        projects_active_q = select(func.count(Project.id)).where(
            Project.tenant_id == self.tenant_id,
            Project.status != "COMPLETED"
        )
        active_projects = self.db.execute(projects_active_q).scalar_one()

        inv_q = select(
            func.coalesce(func.sum(InventoryBalance.quantity), Decimal(0)),
            func.coalesce(func.sum(InventoryBalance.total_cost), Decimal(0))
        ).where(InventoryBalance.tenant_id == self.tenant_id)
        stock_qty, stock_val = self.db.execute(inv_q).one()

        wh_count_q = select(func.count(Warehouse.id)).where(Warehouse.tenant_id == self.tenant_id)
        wh_count = self.db.execute(wh_count_q).scalar_one()

        j_count_q = select(func.count(Journal.id)).where(
            Journal.tenant_id == self.tenant_id,
            Journal.status == JournalStatus.POSTED
        )
        j_count = self.db.execute(j_count_q).scalar_one()

        gl_q = select(
            func.coalesce(func.sum(JournalLine.debit), Decimal(0)),
            func.coalesce(func.sum(JournalLine.credit), Decimal(0))
        ).join(Journal, Journal.id == JournalLine.journal_id).where(
            Journal.tenant_id == self.tenant_id,
            Journal.status == JournalStatus.POSTED
        )
        tot_debits, tot_credits = self.db.execute(gl_q).one()
        is_balanced = (tot_debits == tot_credits)

        ap_q = select(
            func.count(APInvoice.id),
            func.coalesce(func.sum(APInvoice.total_amount), Decimal(0))
        ).where(
            APInvoice.tenant_id == self.tenant_id,
            APInvoice.status == InvoiceStatus.POSTED
        )
        ap_count, ap_open = self.db.execute(ap_q).one()

        clients_count_q = select(func.count(Client.id)).where(Client.tenant_id == self.tenant_id)
        clients_count = self.db.execute(clients_count_q).scalar_one()

        return ExecutiveDashboardReport(
            total_active_contracts=active_contracts,
            total_contract_value=contract_val,
            total_projects=total_projects,
            active_projects=active_projects,
            total_on_hand_quantity=stock_qty,
            total_inventory_valuation=stock_val,
            warehouse_count=wh_count,
            total_journal_entries=j_count,
            total_debits=tot_debits,
            total_credits=tot_credits,
            is_ledger_balanced=is_balanced,
            total_ap_invoices=ap_count,
            total_open_payables=ap_open,
            total_clients=clients_count
        )
