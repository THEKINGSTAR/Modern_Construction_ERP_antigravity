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
    
    lines = relationship("MaterialIssueLine", back_populates="material_issue", cascade="all, delete-orphan", lazy="selectin")
    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id], lazy="selectin")
    project = relationship("Project", foreign_keys=[project_id], lazy="selectin")
    cost_code = relationship("CostCode", foreign_keys=[cost_code_id], lazy="selectin")
    requested_by = relationship("User", foreign_keys=[requested_by_id], lazy="selectin")

    @property
    def warehouse_name(self) -> str:
        return self.warehouse.name if self.warehouse else ""

    @property
    def project_name(self) -> str:
        return self.project.name if self.project else ""

    @property
    def cost_code_code(self) -> str:
        return self.cost_code.code if self.cost_code else ""

    @property
    def cost_code_name(self) -> str:
        return self.cost_code.description if self.cost_code else ""

    @property
    def requested_by_name(self) -> str:
        return self.requested_by.full_name if self.requested_by else ""

    @property
    def lines_count(self) -> int:
        return len(self.lines) if self.lines else 0

    @property
    def total_quantity(self) -> float:
        if not self.lines:
            return 0.0
        return float(sum(line.quantity or 0 for line in self.lines))

    @property
    def total_amount(self) -> float:
        if not self.lines:
            return 0.0
        return float(sum((line.quantity or 0) * (line.unit_cost or 0) for line in self.lines))


class MaterialIssueLine(Base, TenantAwareMixin):
    __tablename__ = "material_issue_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    material_issue_id = Column(Uuid(as_uuid=True), ForeignKey("material_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    
    material_issue = relationship("MaterialIssue", back_populates="lines")
    material = relationship("Material", foreign_keys=[material_id], lazy="selectin")

    @property
    def material_name(self) -> str:
        return self.material.name if self.material else ""

    @property
    def material_code(self) -> str:
        return self.material.material_code if self.material else ""

    @property
    def total_cost(self) -> float:
        return float((self.quantity or 0) * (self.unit_cost or 0))
