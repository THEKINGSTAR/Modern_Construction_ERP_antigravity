import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class InventoryTransferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"

class InventoryTransfer(Base, TenantAwareMixin):
    __tablename__ = "inventory_transfers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_number = Column(String(100), nullable=False, index=True)
    source_warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(InventoryTransferStatus), nullable=False, default=InventoryTransferStatus.DRAFT, index=True)
    
    lines = relationship("InventoryTransferLine", back_populates="inventory_transfer", cascade="all, delete-orphan", lazy="selectin")
    source_warehouse = relationship("Warehouse", foreign_keys=[source_warehouse_id], lazy="selectin")
    destination_warehouse = relationship("Warehouse", foreign_keys=[destination_warehouse_id], lazy="selectin")

    @property
    def source_warehouse_name(self) -> str:
        return self.source_warehouse.name if self.source_warehouse else ""

    @property
    def destination_warehouse_name(self) -> str:
        return self.destination_warehouse.name if self.destination_warehouse else ""

    @property
    def lines_count(self) -> int:
        return len(self.lines) if self.lines else 0

    @property
    def total_amount(self) -> float:
        if not self.lines:
            return 0.0
        return float(sum((line.quantity or 0) * (line.unit_cost or 0) for line in self.lines))


class InventoryTransferLine(Base, TenantAwareMixin):
    __tablename__ = "inventory_transfer_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_transfer_id = Column(Uuid(as_uuid=True), ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    
    inventory_transfer = relationship("InventoryTransfer", back_populates="lines")
    material = relationship("Material", foreign_keys=[material_id], lazy="selectin")

    @property
    def material_name(self) -> str:
        return self.material.name if self.material else ""

    @property
    def material_code(self) -> str:
        return self.material.material_code if self.material else ""
