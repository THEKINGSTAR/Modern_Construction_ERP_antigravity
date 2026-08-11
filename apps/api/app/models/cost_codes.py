import uuid
import enum
from sqlalchemy import Column, String, Uuid, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin, TimestampMixin, AuditMixin

class CostCategory(str, enum.Enum):
    LABOR = "LABOR"
    MATERIAL = "MATERIAL"
    EQUIPMENT = "EQUIPMENT"
    SUBCONTRACT = "SUBCONTRACT"
    OTHER_DIRECT = "OTHER_DIRECT"
    OVERHEAD = "OVERHEAD"

class CostCode(Base, TenantAwareMixin, TimestampMixin, AuditMixin):
    __tablename__ = "cost_codes"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(Uuid(as_uuid=True), ForeignKey("cost_codes.id", ondelete="CASCADE"), nullable=True)
    
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(Enum(CostCategory, name="cost_category_enum", create_type=False), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    children = relationship("CostCode", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("CostCode", back_populates="children", remote_side=[id])
