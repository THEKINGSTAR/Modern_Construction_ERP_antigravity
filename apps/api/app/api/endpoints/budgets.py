from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_tenant
from app.models.budgets import Budget, BudgetLine
from app.schemas.budgets import (
    BudgetCreate, BudgetResponse, BudgetUpdate, BudgetWithLinesResponse,
    BudgetLineCreate, BudgetLineResponse, BudgetLineUpdate
)
from app.services.budget_projections import BudgetProjectionService

router = APIRouter()

@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_in: BudgetCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["budgets.create"]))
):
    db_budget = Budget(**budget_in.model_dump(), tenant_id=tenant_id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["budgets.read"]))
):
    return db.query(Budget).filter(Budget.tenant_id == tenant_id).all()

@router.get("/{id}", response_model=BudgetResponse)
def get_budget(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["budgets.read"]))
):
    budget = db.query(Budget).filter(Budget.id == id, Budget.tenant_id == tenant_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@router.post("/{id}/lines", response_model=BudgetLineResponse, status_code=status.HTTP_201_CREATED)
def create_budget_line(
    id: UUID,
    line_in: BudgetLineCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["budgets.update"]))
):
    budget = db.query(Budget).filter(Budget.id == id, Budget.tenant_id == tenant_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    db_line = BudgetLine(
        **line_in.model_dump(),
        budget_id=id,
        tenant_id=tenant_id
    )
    db.add(db_line)
    db.commit()
    db.refresh(db_line)
    
    # Calculate computed fields for response
    return enrich_budget_line(db_line, budget.project_id, tenant_id, db=db)

@router.get("/{id}/summary", response_model=BudgetWithLinesResponse)
def get_budget_summary(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["budgets.read"]))
):
    budget = db.query(Budget).filter(Budget.id == id, Budget.tenant_id == tenant_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    lines = db.query(BudgetLine).filter(BudgetLine.budget_id == id).all()
    enriched_lines = [enrich_budget_line(line, budget.project_id, tenant_id, db=db) for line in lines]
    
    # We construct a dictionary matching the schema to leverage from_attributes if needed, 
    # but Pydantic parses dictionaries natively anyway.
    result = {
        "id": budget.id,
        "name": budget.name,
        "project_id": budget.project_id,
        "status": budget.status,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
        "created_by": budget.created_by,
        "updated_by": budget.updated_by,
        "lines": enriched_lines
    }
    return result

def enrich_budget_line(db_line: BudgetLine, project_id: UUID, tenant_id: UUID, db: Optional[Session] = None) -> dict:
    current_budget = db_line.original_budget + db_line.approved_changes
    committed_cost = BudgetProjectionService.get_committed_cost(project_id, db_line.cost_code_id, tenant_id, db=db)
    actual_cost = BudgetProjectionService.get_actual_cost(project_id, db_line.cost_code_id, tenant_id, db=db)
    forecast_cost = BudgetProjectionService.get_forecast_cost(project_id, db_line.cost_code_id, tenant_id, db=db)
    
    # Variance = Current Budget - (Actual Cost + Committed Cost) - or whatever variance formula we want
    # Usually: Variance = Current Budget - Forecast Cost
    # If Forecast Cost defaults to 0, let's use:
    # Variance = Current Budget - (Committed + Actual) for now, or just follow standard
    variance = current_budget - (committed_cost + actual_cost)
    if forecast_cost > 0:
        variance = current_budget - forecast_cost
        
    return {
        "id": db_line.id,
        "budget_id": db_line.budget_id,
        "cost_code_id": db_line.cost_code_id,
        "original_budget": db_line.original_budget,
        "approved_changes": db_line.approved_changes,
        "current_budget": current_budget,
        "committed_cost": committed_cost,
        "actual_cost": actual_cost,
        "forecast_cost": forecast_cost,
        "variance": variance,
        "created_at": db_line.created_at,
        "updated_at": db_line.updated_at,
        "created_by": db_line.created_by,
        "updated_by": db_line.updated_by
    }
