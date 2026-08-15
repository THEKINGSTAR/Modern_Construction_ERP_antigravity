from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.approvals import ApprovalRule, ApprovalDelegation
from app.schemas.approvals import (
    ApprovalRuleCreate, ApprovalRuleResponse,
    ApprovalDelegationCreate, ApprovalDelegationResponse,
    ApprovalWorkflowResponse, ApprovalAction
)
from app.services.approval_service import ApprovalService

router = APIRouter()

@router.post("/rules", response_model=ApprovalRuleResponse, status_code=201)
def create_approval_rule(
    data: ApprovalRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rule = ApprovalRule(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.post("/delegations", response_model=ApprovalDelegationResponse, status_code=201)
def create_delegation(
    data: ApprovalDelegationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    delg = ApprovalDelegation(**data.model_dump(), tenant_id=current_user.tenant_id)
    db.add(delg)
    db.commit()
    db.refresh(delg)
    return delg

@router.post("/workflows", response_model=ApprovalWorkflowResponse, status_code=201)
def create_workflow(
    entity_type: str,
    entity_id: UUID,
    amount: float = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db, current_user.tenant_id, current_user.id)
    return service.create_workflow(entity_type, entity_id, amount)

@router.post("/workflows/{workflow_id}/action", response_model=ApprovalWorkflowResponse)
def process_workflow_action(
    workflow_id: UUID,
    data: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ApprovalService(db, current_user.tenant_id, current_user.id)
    return service.process_action(workflow_id, data.action, data.comments)
