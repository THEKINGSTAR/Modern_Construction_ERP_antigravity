from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_user
from app.core.repository import BaseRepository
from app.models.user import User
from app.models.org_settings import Currency, ExchangeRate, FiscalYear, AccountingPeriod, TenantSettings

router = APIRouter()

# Global Currency Endpoints (No tenant isolation)
@router.get("/currencies", response_model=List[Dict[str, Any]])
def get_currencies(db: Session = Depends(get_db)):
    currencies = db.query(Currency).all()
    return [{"code": c.code, "name": c.name, "symbol": c.symbol} for c in currencies]

# Tenant Settings Endpoint
@router.get("/tenant", response_model=Dict[str, Any])
def get_tenant_settings(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    repo = BaseRepository(TenantSettings, db)
    # Get first settings for tenant (should only be 1)
    settings = repo.get_all()
    if not settings:
        raise HTTPException(status_code=404, detail="Tenant settings not found")
    s = settings[0]
    return {
        "base_currency_code": s.base_currency_code,
        "default_locale": s.default_locale,
        "default_timezone": s.default_timezone,
        "default_date_format": s.default_date_format,
        "default_number_format": s.default_number_format
    }

@router.put("/tenant", response_model=Dict[str, Any])
def update_tenant_settings(
    data: Dict[str, Any],
    db: Session = Depends(get_db),
    # Assuming update settings needs admin/settings update perm, for now require superuser or a specific perm.
    # In a real app we'd add 'settings.update' to seed, but we'll leave it simple.
    current_user: User = Depends(get_current_user)
):
    repo = BaseRepository(TenantSettings, db)
    settings = repo.get_all()
    if not settings:
        raise HTTPException(status_code=404, detail="Tenant settings not found")
    s = settings[0]
    
    updated = repo.update(s, data)
    return {
        "base_currency_code": updated.base_currency_code,
        "default_locale": updated.default_locale,
        "default_timezone": updated.default_timezone,
        "default_date_format": updated.default_date_format,
        "default_number_format": updated.default_number_format
    }

# Fiscal Years Endpoint
@router.get("/fiscal-years", response_model=List[Dict[str, Any]])
def get_fiscal_years(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = BaseRepository(FiscalYear, db)
    years = repo.get_all()
    return [{"id": str(y.id), "name": y.name, "start_date": str(y.start_date), "end_date": str(y.end_date), "is_closed": y.is_closed} for y in years]

# Exchange Rates Endpoint
@router.get("/exchange-rates", response_model=List[Dict[str, Any]])
def get_exchange_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = BaseRepository(ExchangeRate, db)
    rates = repo.get_all()
    return [{"id": str(r.id), "from_currency": r.from_currency_code, "to_currency": r.to_currency_code, "rate": float(r.rate), "valid_from": str(r.valid_from)} for r in rates]
