import uuid
from sqlalchemy import Column, String, Uuid, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class WBSNode(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "wbs_nodes"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("wbs_nodes.id", ondelete="CASCADE"), nullable=True)
    
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    project = relationship("Project")
    children = relationship("WBSNode", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("WBSNode", back_populates="children", remote_side=[id])
