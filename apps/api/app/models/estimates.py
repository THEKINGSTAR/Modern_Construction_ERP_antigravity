import uuid
from sqlalchemy import Column, String, Uuid, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class Estimate(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "estimates"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    current_revision_id = Column(Uuid(as_uuid=True), ForeignKey("estimate_revisions.id", use_alter=True, ondelete="SET NULL"), nullable=True)
    
    project = relationship("Project")
    revisions = relationship("EstimateRevision", back_populates="estimate", foreign_keys="EstimateRevision.estimate_id", cascade="all, delete-orphan")
    current_revision = relationship("EstimateRevision", foreign_keys=[current_revision_id], post_update=True)

class EstimateRevision(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "estimate_revisions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estimate_id = Column(Uuid(as_uuid=True), ForeignKey("estimates.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="DRAFT", nullable=False)
    
    estimate = relationship("Estimate", back_populates="revisions", foreign_keys=[estimate_id])
    items = relationship("EstimateItem", back_populates="revision", cascade="all, delete-orphan")

class EstimateItem(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "estimate_items"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = Column(Uuid(as_uuid=True), ForeignKey("estimate_revisions.id", ondelete="CASCADE"), nullable=False)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="SET NULL"), nullable=True)
    
    item_code = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    unit_rate = Column(Numeric(18, 4), nullable=False, default=0)
    amount = Column(Numeric(18, 4), nullable=False, default=0)
    
    revision = relationship("EstimateRevision", back_populates="items")
    cost_code = relationship("CostCode")
