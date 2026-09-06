from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.schemas.purchase_orders import PurchaseOrderCreate, PurchaseOrderResponse

router = APIRouter()

@router.post("/", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    if not po_in.lines:
        raise HTTPException(status_code=400, detail="PO must have at least one line")

    total_amount = sum(line.amount for line in po_in.lines)
    
    po = PurchaseOrder(
        po_number=po_in.po_number,
        project_id=po_in.project_id,
        supplier_id=po_in.supplier_id,
        quotation_id=po_in.quotation_id,
        status=POStatus.DRAFT,
        issue_date=po_in.issue_date,
        delivery_date=po_in.delivery_date,
        total_amount=total_amount,
        currency=po_in.currency,
        notes=po_in.notes
    )
    db.add(po)
    db.flush()

    for line_in in po_in.lines:
        # Prevent floating point mismatch: quantity * unit_price must equal amount
        if abs(line_in.quantity * line_in.unit_price - line_in.amount) > Decimal('0.0001'):
            raise HTTPException(status_code=400, detail="Line amount must exactly equal quantity * unit_price")

        line = PurchaseOrderLine(
            purchase_order_id=po.id,
            cost_code_id=line_in.cost_code_id,
            item_description=line_in.item_description,
            unit=line_in.unit,
            quantity=line_in.quantity,
            unit_price=line_in.unit_price,
            amount=line_in.amount
        )
        db.add(line)
    
    db.commit()
    db.refresh(po)
    return po

@router.get("/{po_id}", response_model=PurchaseOrderResponse)
def get_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po

@router.post("/{po_id}/issue")
def issue_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    if po.status != POStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT POs can be issued")
    
    po.status = POStatus.ISSUED
    db.commit()
    return {"status": "success"}

@router.post("/{po_id}/cancel")
def cancel_purchase_order(
    po_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id, PurchaseOrder.tenant_id == tenant_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    if po.status in (POStatus.COMPLETED, POStatus.CANCELLED):
        raise HTTPException(status_code=400, detail="Cannot cancel a completed or already cancelled PO")
    
    po.status = POStatus.CANCELLED
    db.commit()
    return {"status": "success"}

@router.get("/", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    return db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id).all()
