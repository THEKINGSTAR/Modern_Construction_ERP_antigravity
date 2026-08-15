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
    cost_code_id: UUID4
    date: date
    amount: Decimal
    currency: str
    source_type: str
    source_id: UUID4
    cost_type: str

class CostCodeSummaryResponse(BaseModel):
    cost_code_id: UUID4
    original_budget: Decimal
    approved_changes: Decimal
    current_budget: Decimal
    committed_cost: Decimal
    actual_cost: Decimal
    estimate_to_complete: Decimal
    estimate_at_completion: Decimal
    variance: Decimal
