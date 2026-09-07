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
    
    lines = relationship("GoodsReceiptLine", back_populates="goods_receipt", cascade="all, delete-orphan", lazy="selectin")
    purchase_order = relationship("PurchaseOrder", foreign_keys=[purchase_order_id], lazy="selectin")
    supplier = relationship("Supplier", foreign_keys=[supplier_id], lazy="selectin")
    warehouse = relationship("Warehouse", foreign_keys=[warehouse_id], lazy="selectin")

    @property
    def po_number(self) -> str:
        return self.purchase_order.po_number if self.purchase_order else ""

    @property
    def supplier_name(self) -> str:
        return self.supplier.name if self.supplier else ""

    @property
    def warehouse_name(self) -> str:
        return self.warehouse.name if self.warehouse else ""

    @property
    def lines_count(self) -> int:
        return len(self.lines) if self.lines else 0

    @property
    def total_received_amount(self) -> float:
        if not self.lines:
            return 0.0
        return float(sum((line.accepted_quantity or 0) * (line.unit_cost or 0) for line in self.lines))


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
    material = relationship("Material", foreign_keys=[material_id], lazy="selectin")

    @property
    def material_name(self) -> str:
        return self.material.name if self.material else ""

    @property
    def material_code(self) -> str:
        return self.material.material_code if self.material else ""

    @property
    def total_cost(self) -> float:
        return float((self.accepted_quantity or 0) * (self.unit_cost or 0))
