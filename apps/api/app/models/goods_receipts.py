import uuid
import enum
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Enum, Uuid, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.models import TenantAwareMixin

class GoodsReceiptStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"

class GoodsReceipt(Base, TenantAwareMixin):
    __tablename__ = "goods_receipts"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_number = Column(String(100), nullable=False, index=True)
    purchase_order_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    supplier_id = Column(Uuid(as_uuid=True), ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    warehouse_id = Column(Uuid(as_uuid=True), ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(GoodsReceiptStatus), nullable=False, default=GoodsReceiptStatus.DRAFT, index=True)
    
    lines = relationship("GoodsReceiptLine", back_populates="goods_receipt", cascade="all, delete-orphan")


class GoodsReceiptLine(Base, TenantAwareMixin):
    __tablename__ = "goods_receipt_lines"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goods_receipt_id = Column(Uuid(as_uuid=True), ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_order_line_id = Column(Uuid(as_uuid=True), ForeignKey("purchase_order_lines.id", ondelete="RESTRICT"), nullable=False, index=True)
    material_id = Column(Uuid(as_uuid=True), ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    received_quantity = Column(Numeric(18, 4), nullable=False)
    accepted_quantity = Column(Numeric(18, 4), nullable=False)
    rejected_quantity = Column(Numeric(18, 4), nullable=False, default=0)
    unit_cost = Column(Numeric(18, 4), nullable=False)
    notes = Column(Text, nullable=True)
    
    goods_receipt = relationship("GoodsReceipt", back_populates="lines")
