import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class MaterialIssueStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"

class MaterialIssue(Base, TenantAwareMixin):
    __tablename__ = "material_issues"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_number = Column(String(100), nullable=False, index=True)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="RESTRICT"), nullable=False, index=True)
    cost_code_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    purpose = Column(Text, nullable=True)
    requested_by_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(Enum(MaterialIssueStatus), nullable=False, default=MaterialIssueStatus.DRAFT, index=True)
    
    lines = relationship("MaterialIssueLine", back_populates="material_issue", cascade="all, delete-orphan")


class MaterialIssueLine(Base, TenantAwareMixin):
    __tablename__ = "material_issue_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_issue_id = Column(Uuid(as_uuid=True), ForeignKey("material_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0) # Automatically set upon posting
    notes = Column(Text, nullable=True)
    
    material_issue = relationship("MaterialIssue", back_populates="lines")
