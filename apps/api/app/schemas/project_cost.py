from pydantic import BaseModel, UUID4, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.models.forecasts import ForecastStatus

# Forecast Schemas
class ProjectForecastLineCreate(BaseModel):
    cost_code_id: UUID4
    etc_amount: Decimal
    notes: Optional[str] = None

class ProjectForecastCreate(BaseModel):
    forecast_number: str
    date: date
    notes: Optional[str] = None
    lines: List[ProjectForecastLineCreate]

class ProjectForecastResponse(BaseModel):
    id: UUID4
    project_id: UUID4
    forecast_number: str
    date: date
    status: ForecastStatus
    
    class Config:
        from_attributes = True

# Cost Aggregation Schemas
class CostTransactionResponse(BaseModel):
    project_id: UUID4
    cost_code_id: Optional[UUID4] = None
    cost_code_code: Optional[str] = None
    cost_code_name: Optional[str] = None
    date: date
    amount: Decimal
    currency: str
    source_type: str
    source_id: UUID4
    source_reference: Optional[str] = None
    cost_type: str

class CostCodeSummaryResponse(BaseModel):
    cost_code_id: UUID4
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
    variance_percentage: Optional[Decimal] = Decimal("0.0")
    status: Optional[str] = "ON_TRACK"

class ProjectCostKPISummary(BaseModel):
    project_id: UUID4
    project_name: str
    project_number: Optional[str] = None
    total_original_budget: Decimal = Decimal("0.0")
    total_approved_changes: Decimal = Decimal("0.0")
    total_current_budget: Decimal = Decimal("0.0")
    total_committed: Decimal = Decimal("0.0")
    total_actual: Decimal = Decimal("0.0")
    total_estimate_to_complete: Decimal = Decimal("0.0")
    total_estimate_at_completion: Decimal = Decimal("0.0")
    total_variance: Decimal = Decimal("0.0")
    cost_performance_index: Decimal = Decimal("1.0")
    status: str = "ON_TRACK"

class PortfolioCostSummaryResponse(BaseModel):
    total_projects: int = 0
    total_budget: Decimal = Decimal("0.0")
    total_committed: Decimal = Decimal("0.0")
    total_actual: Decimal = Decimal("0.0")
    total_etc: Decimal = Decimal("0.0")
    total_eac: Decimal = Decimal("0.0")
    total_variance: Decimal = Decimal("0.0")
    overall_cpi: Decimal = Decimal("1.0")
    projects: List[ProjectCostKPISummary] = []
