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
    
    lines = relationship("InventoryTransferLine", back_populates="inventory_transfer", cascade="all, delete-orphan")


class InventoryTransferLine(Base, TenantAwareMixin):
    __tablename__ = "inventory_transfer_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inventory_transfer_id = Column(Uuid(as_uuid=True), ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False, default=0) # Automatically set upon posting
    notes = Column(Text, nullable=True)
    
    inventory_transfer = relationship("InventoryTransfer", back_populates="lines")
