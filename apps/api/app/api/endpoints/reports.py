from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.schemas.reports import (
    ProjectDashboardMetrics, BudgetVsActualReport, AgingReport, TrialBalanceReport, ExecutiveDashboardReport
)
from app.services.reporting_service import ReportingService

router = APIRouter(tags=["Reports"])

@router.get("/projects/{project_id}/dashboard", response_model=ProjectDashboardMetrics)
def get_project_dashboard(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    service = ReportingService(db, tenant_id)
    return service.get_project_dashboard(project_id)

@router.get("/projects/{project_id}/budget-vs-actual", response_model=BudgetVsActualReport)
def get_budget_vs_actual(
    project_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    service = ReportingService(db, tenant_id)
    return service.get_budget_vs_actual(project_id)

@router.get("/accounting/ap-aging", response_model=AgingReport)
def get_ap_aging(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    if not as_of_date:
        as_of_date = date.today()
    service = ReportingService(db, tenant_id)
    return service.get_ap_aging(as_of_date)

@router.get("/accounting/trial-balance", response_model=TrialBalanceReport)
def get_trial_balance(
    as_of_date: date = None,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    if not as_of_date:
        as_of_date = date.today()
    service = ReportingService(db, tenant_id)
    return service.get_trial_balance(as_of_date)

@router.get("/executive-dashboard", response_model=ExecutiveDashboardReport)
def get_executive_dashboard(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    service = ReportingService(db, tenant_id)
    return service.get_executive_dashboard()
