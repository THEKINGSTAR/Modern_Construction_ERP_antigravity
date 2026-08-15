from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.models.approvals import ApprovalWorkflowStatus, ApprovalStepStatus

class ApprovalRuleBase(BaseModel):
    entity_type: str
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    required_role: str
    step_order: int

class ApprovalRuleCreate(ApprovalRuleBase):
    pass

class ApprovalRuleResponse(ApprovalRuleBase):
    id: UUID

    class Config:
        from_attributes = True

class ApprovalStepResponse(BaseModel):
    id: UUID
    step_order: int
    required_role: str
    approver_id: Optional[UUID] = None
    status: ApprovalStepStatus
    comments: Optional[str] = None
    acted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ApprovalWorkflowResponse(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    status: ApprovalWorkflowStatus
    current_step_order: int
    steps: List[ApprovalStepResponse] = []

    class Config:
        from_attributes = True

class ApprovalAction(BaseModel):
    action: str  # "APPROVE" or "REJECT"
    comments: Optional[str] = None

class ApprovalDelegationBase(BaseModel):
    delegator_id: UUID
    delegatee_id: UUID
    start_date: datetime
    end_date: datetime

class ApprovalDelegationCreate(ApprovalDelegationBase):
    pass

class ApprovalDelegationResponse(ApprovalDelegationBase):
    id: UUID

    class Config:
        from_attributes = True
