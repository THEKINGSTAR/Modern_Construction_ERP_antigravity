from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.schemas.project_cost import (
    ProjectForecastCreate, ProjectForecastResponse,
    CostTransactionResponse, CostCodeSummaryResponse,
    ProjectCostKPISummary, PortfolioCostSummaryResponse
)
from app.models.forecasts import ProjectForecast, ProjectForecastLine, ForecastStatus
from app.services.project_cost import ProjectCostEngine

router = APIRouter(tags=["Project Cost"])

@router.get("/portfolio/summary", response_model=PortfolioCostSummaryResponse)
def get_portfolio_cost_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    engine = ProjectCostEngine(db, tenant_id)
    return engine.get_portfolio_cost_summary()

@router.get("/projects/{project_id}/costs/kpi", response_model=ProjectCostKPISummary)
def get_project_cost_kpis(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    engine = ProjectCostEngine(db, tenant_id)
    return engine.get_project_kpi_summary(project_id)

@router.post("/projects/{project_id}/forecasts", response_model=ProjectForecastResponse, status_code=status.HTTP_201_CREATED)
def create_project_forecast(
    project_id: UUID,
    forecast: ProjectForecastCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    # 0. Supersede previous approved forecasts for this project
    db.query(ProjectForecast).filter(
        ProjectForecast.tenant_id == tenant_id,
        ProjectForecast.project_id == project_id,
        ProjectForecast.status == ForecastStatus.APPROVED
    ).update({"status": ForecastStatus.SUPERSEDED})

    # 1. Create Forecast Document
    db_forecast = ProjectForecast(
        tenant_id=tenant_id,
        project_id=project_id,
        forecast_number=forecast.forecast_number,
        date=forecast.date,
        notes=forecast.notes,
        status=ForecastStatus.APPROVED, # MVP: auto-approve
        created_by=current_user.id
    )
    db.add(db_forecast)
    db.flush()

    # 2. Add Lines
    for line in forecast.lines:
        db_line = ProjectForecastLine(
            tenant_id=tenant_id,
            forecast_id=db_forecast.id,
            cost_code_id=line.cost_code_id,
            etc_amount=line.etc_amount,
            notes=line.notes,
            created_by=current_user.id
        )
        db.add(db_line)

    db.commit()
    db.refresh(db_forecast)
    return db_forecast

@router.get("/projects/{project_id}/costs/transactions", response_model=List[CostTransactionResponse])
def get_project_cost_transactions(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    engine = ProjectCostEngine(db, tenant_id)
    return engine.get_cost_transactions(project_id)

@router.get("/projects/{project_id}/costs/summary", response_model=List[CostCodeSummaryResponse])
def get_project_cost_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    engine = ProjectCostEngine(db, tenant_id)
    return engine.get_project_cost_summary(project_id)
