from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.bank import (
    BankAccountCreate, BankAccountResponse,
    BankTransactionCreate, BankTransactionResponse,
    BankStatementCreate, BankStatementResponse,
    ReconciliationMatchRequest, BankStatementLineResponse
)
from app.services.bank_service import BankService

router = APIRouter()

@router.post("/accounts", response_model=BankAccountResponse, status_code=201)
def create_bank_account(
    account: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.create_bank_account(account)

@router.post("/transactions", response_model=BankTransactionResponse, status_code=201)
def record_transaction(
    transaction: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.record_transaction(transaction)

@router.post("/statements", response_model=BankStatementResponse, status_code=201)
def import_statement(
    statement: BankStatementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.import_statement(statement)

@router.post("/reconciliation/match", response_model=BankStatementLineResponse)
def match_transaction(
    request: ReconciliationMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.match_transaction(request)

@router.post("/statements/{statement_id}/reconcile", response_model=BankStatementResponse)
def reconcile_statement(
    statement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.reconcile_statement(statement_id)
