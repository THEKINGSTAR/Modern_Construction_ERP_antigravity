import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class InventoryAdjustmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"

class AdjustmentType(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"

class InventoryAdjustment(Base, TenantAwareMixin):
    __tablename__ = "inventory_adjustments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    adjustment_number = Column(String(100), nullable=False, index=True)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    reason = Column(Text, nullable=True)
    status = Column(Enum(InventoryAdjustmentStatus), nullable=False, default=InventoryAdjustmentStatus.DRAFT, index=True)
    
    lines = relationship("InventoryAdjustmentLine", back_populates="inventory_adjustment", cascade="all, delete-orphan")


class InventoryAdjustmentLine(Base, TenantAwareMixin):
    __tablename__ = "inventory_adjustment_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_adjustment_id = Column(Uuid(as_uuid=True), ForeignKey("inventory_adjustments.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    adjustment_type = Column(Enum(AdjustmentType), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    notes = Column(Text, nullable=True)
    
    inventory_adjustment = relationship("InventoryAdjustment", back_populates="lines")
