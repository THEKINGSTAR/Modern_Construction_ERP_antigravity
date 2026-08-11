import uuid
from sqlalchemy import Column, String, Uuid, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class Budget(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "budgets"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    
    project = relationship("Project")
    lines = relationship("BudgetLine", back_populates="budget", cascade="all, delete-orphan")

class BudgetLine(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "budget_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = Column(Uuid(as_uuid=True), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="RESTRICT"), nullable=False)
    
    original_budget = Column(Numeric(18, 4), nullable=False, default=0)
    approved_changes = Column(Numeric(18, 4), nullable=False, default=0)
    
    budget = relationship("Budget", back_populates="lines")
    cost_code = relationship("CostCode")
