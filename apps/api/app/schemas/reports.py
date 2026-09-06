from pydantic import BaseModel
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date
from decimal import Decimal

class ProjectDashboardMetrics(BaseModel):
    project_id: UUID
    contract_value: Decimal = Decimal(0)
    current_contract_value: Decimal = Decimal(0)
    original_budget: Decimal = Decimal(0)
    current_budget: Decimal = Decimal(0)
    committed_cost: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    forecast_cost: Decimal = Decimal(0) # ETC
    estimate_at_completion: Decimal = Decimal(0) # EAC
    variance: Decimal = Decimal(0)
    billed: Decimal = Decimal(0)
    collected: Decimal = Decimal(0)
    receivable: Decimal = Decimal(0)
    payable: Decimal = Decimal(0)
    gross_profit: Decimal = Decimal(0)
    margin_percentage: Decimal = Decimal(0)

class CostCodeDetail(BaseModel):
    cost_code_id: UUID
    cost_code_name: str
    original_budget: Decimal = Decimal(0)
    current_budget: Decimal = Decimal(0)
    actual_cost: Decimal = Decimal(0)
    variance: Decimal = Decimal(0)

class BudgetVsActualReport(BaseModel):
    project_id: UUID
    project_name: str
    total_budget: Decimal = Decimal(0)
    total_actual: Decimal = Decimal(0)
    total_variance: Decimal = Decimal(0)
    details: List[CostCodeDetail] = []

class CommitmentDetail(BaseModel):
    source_type: str
    source_id: UUID
    reference: str
    supplier_name: str
    original_value: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)
    invoiced_amount: Decimal = Decimal(0)
    remaining_commitment: Decimal = Decimal(0)

class CommitmentReport(BaseModel):
    project_id: UUID
    commitments: List[CommitmentDetail] = []
    total_remaining: Decimal = Decimal(0)

class AgingBucket(BaseModel):
    current: Decimal = Decimal(0)
    days_1_30: Decimal = Decimal(0)
    days_31_60: Decimal = Decimal(0)
    days_61_90: Decimal = Decimal(0)
    over_90: Decimal = Decimal(0)
    total: Decimal = Decimal(0)

class AgingDetail(BaseModel):
    party_id: UUID
    party_name: str
    buckets: AgingBucket

class AgingReport(BaseModel):
    as_of_date: date
    type: str # AP or AR
    details: List[AgingDetail] = []
    totals: AgingBucket

class TrialBalanceLine(BaseModel):
    account_id: UUID
    account_code: str
    account_name: str
    debit: Decimal = Decimal(0)
    credit: Decimal = Decimal(0)

class TrialBalanceReport(BaseModel):
    as_of_date: date
    lines: List[TrialBalanceLine] = []
    total_debit: Decimal = Decimal(0)
    total_credit: Decimal = Decimal(0)

class ExecutiveDashboardReport(BaseModel):
    total_active_contracts: int = 0
    total_contract_value: Decimal = Decimal(0)
    total_projects: int = 0
    active_projects: int = 0
    total_on_hand_quantity: Decimal = Decimal(0)
    total_inventory_valuation: Decimal = Decimal(0)
    warehouse_count: int = 0
    total_journal_entries: int = 0
    total_debits: Decimal = Decimal(0)
    total_credits: Decimal = Decimal(0)
    is_ledger_balanced: bool = True
    total_ap_invoices: int = 0
    total_open_payables: Decimal = Decimal(0)
    total_clients: int = 0
