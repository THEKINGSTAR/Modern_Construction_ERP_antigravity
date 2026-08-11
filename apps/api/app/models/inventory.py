import uuid
import enum
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, Uuid
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.models import TenantAwareMixin

class TransactionType(str, enum.Enum):
    OPENING = "OPENING"
    RECEIPT = "RECEIPT"
    ISSUE = "ISSUE"
    TRANSFER_OUT = "TRANSFER_OUT"
    TRANSFER_IN = "TRANSFER_IN"
    RETURN = "RETURN"
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"

class InventoryTransaction(Base, TenantAwareMixin):
    __tablename__ = "inventory_transactions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    total_cost = Column(Numeric(18, 4), nullable=False)
    
    reference_type = Column(String(50), nullable=True, index=True) # e.g. GOODS_RECEIPT, MATERIAL_ISSUE
    reference_id = Column(Uuid(as_uuid=True), nullable=True, index=True)
    
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)


class InventoryBalance(Base, TenantAwareMixin):
    __tablename__ = "inventory_balances"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    quantity = Column(Numeric(18, 4), nullable=False, default=0)
    total_cost = Column(Numeric(18, 4), nullable=False, default=0)
