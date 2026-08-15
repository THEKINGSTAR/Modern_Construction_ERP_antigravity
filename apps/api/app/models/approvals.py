from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, Enum, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from app.core.database import Base

class ApprovalWorkflowStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class ApprovalStepStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ApprovalRule(Base):
    __tablename__ = "approval_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    entity_type = Column(String, nullable=False)
    min_amount = Column(Numeric(15, 2), nullable=True)
    max_amount = Column(Numeric(15, 2), nullable=True)
    
    required_role = Column(String, nullable=False)
    step_order = Column(Integer, nullable=False)

class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    entity_type = Column(String, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    status = Column(String, default=ApprovalWorkflowStatus.PENDING.value, nullable=False)
    current_step_order = Column(Integer, default=1, nullable=False)
    
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan", order_by="ApprovalStep.step_order")

class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("approval_workflows.id"), nullable=False)
    
    step_order = Column(Integer, nullable=False)
    required_role = Column(String, nullable=False)
    
    approver_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String, default=ApprovalStepStatus.PENDING.value, nullable=False)
    comments = Column(Text, nullable=True)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    
    workflow = relationship("ApprovalWorkflow", back_populates="steps")

class ApprovalDelegation(Base):
    __tablename__ = "approval_delegations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    delegator_id = Column(UUID(as_uuid=True), nullable=False)
    delegatee_id = Column(UUID(as_uuid=True), nullable=False)
    
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
