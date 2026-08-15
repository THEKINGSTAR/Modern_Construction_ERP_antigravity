from typing import List, Any
from uuid import UUID
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant as get_tenant_id
from app.models.user import User
from app.schemas.accounting import JournalCreate, JournalResponse, GLBalanceResponse, GLBalanceQuery
from app.services.accounting import AccountingEngine

router = APIRouter()

class ReverseJournalRequest(BaseModel):
    reversal_date: date
    description: str

@router.post("/journals", response_model=JournalResponse)
def create_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_in: JournalCreate,
    auto_post: bool = False
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    journal = engine.create_journal(journal_in, auto_post=auto_post)
    db.commit()
    db.refresh(journal)
    return journal

@router.post("/journals/{journal_id}/post", response_model=JournalResponse)
def post_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_id: UUID
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    journal = engine.post_journal(journal_id)
    db.commit()
    db.refresh(journal)
    return journal

@router.post("/journals/{journal_id}/reverse", response_model=JournalResponse)
def reverse_journal(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    journal_id: UUID,
    request: ReverseJournalRequest
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    journal = engine.reverse_journal(journal_id, request.reversal_date, request.description)
    db.commit()
    db.refresh(journal)
    return journal

@router.post("/gl/balances", response_model=List[GLBalanceResponse])
def get_gl_balances(
    *,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    query: GLBalanceQuery
) -> Any:
    engine = AccountingEngine(db, tenant_id, current_user.id)
    balances = engine.get_gl_balances(
        start_date=query.start_date,
        end_date=query.end_date,
        account_id=query.account_id,
        project_id=query.project_id,
        department_id=query.department_id,
        branch_id=query.branch_id,
        business_unit_id=query.business_unit_id
    )
    return balances
