import uuid
from sqlalchemy import Column, String, Uuid, ForeignKey, Numeric, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class BOQ(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "boqs"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    current_revision_id = Column(Uuid(as_uuid=True), ForeignKey("boq_revisions.id", use_alter=True, ondelete="SET NULL"), nullable=True)
    
    project = relationship("Project")
    revisions = relationship("BOQRevision", back_populates="boq", foreign_keys="BOQRevision.boq_id", cascade="all, delete-orphan")
    current_revision = relationship("BOQRevision", foreign_keys=[current_revision_id], post_update=True)

class BOQRevision(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "boq_revisions"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    boq_id = Column(Uuid(as_uuid=True), ForeignKey("boqs.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    status = Column(String(50), default="DRAFT", nullable=False)
    
    boq = relationship("BOQ", back_populates="revisions", foreign_keys=[boq_id])
    items = relationship("BOQItem", back_populates="revision", cascade="all, delete-orphan")

class BOQItem(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "boq_items"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    revision_id = Column(Uuid(as_uuid=True), ForeignKey("boq_revisions.id", ondelete="CASCADE"), nullable=False)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="SET NULL"), nullable=True)
    
    item_code = Column(String(100), nullable=False)
    description = Column(String(1000), nullable=False)
    unit = Column(String(50), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    unit_rate = Column(Numeric(18, 4), nullable=False, default=0)
    amount = Column(Numeric(18, 4), nullable=False, default=0)
    
    revision = relationship("BOQRevision", back_populates="items")
    cost_code = relationship("CostCode")
