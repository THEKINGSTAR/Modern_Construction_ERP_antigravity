from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.suppliers import Supplier
from app.models.requisitions import PurchaseRequisition, PRStatus
from app.schemas.purchase_orders import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    ProcurementSummaryResponse
)

router = APIRouter()

@router.get("/summary", response_model=ProcurementSummaryResponse)
def get_procurement_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    total_val = db.query(func.coalesce(func.sum(PurchaseOrder.total_amount), 0)).filter(
        PurchaseOrder.tenant_id == tenant_id,
        PurchaseOrder.status != POStatus.CANCELLED
    ).scalar() or Decimal('0.0000')

    active_pos = db.query(func.count(PurchaseOrder.id)).filter(
        PurchaseOrder.tenant_id == tenant_id,
        PurchaseOrder.status != POStatus.CANCELLED
    ).scalar() or 0

    pending_reqs = db.query(func.count(PurchaseRequisition.id)).filter(
        PurchaseRequisition.tenant_id == tenant_id,
        PurchaseRequisition.status.in_([PRStatus.DRAFT, PRStatus.SUBMITTED])
    ).scalar() or 0

    app_suppliers = db.query(func.count(Supplier.id)).filter(
        Supplier.tenant_id == tenant_id,
        Supplier.status == 'ACTIVE'
    ).scalar() or 0

    total_suppliers = db.query(func.count(Supplier.id)).filter(
        Supplier.tenant_id == tenant_id
    ).scalar() or 0

    recent_pos = db.query(PurchaseOrder).filter(
        PurchaseOrder.tenant_id == tenant_id
    ).order_by(PurchaseOrder.created_at.desc()).limit(10).all()

    return ProcurementSummaryResponse(
        total_po_value=Decimal(str(total_val)),
        active_pos_count=active_pos,
        pending_requisitions_count=pending_reqs,
        approved_suppliers_count=app_suppliers,
        total_suppliers_count=total_suppliers,
        recent_pos=recent_pos
    )

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
        tenant_id=tenant_id,
        po_number=po_in.po_number,
        project_id=po_in.project_id,
        supplier_id=po_in.supplier_id,
        quotation_id=po_in.quotation_id,
        status=POStatus.DRAFT,
        issue_date=po_in.issue_date,
        delivery_date=po_in.delivery_date,
        total_amount=total_amount,
        currency=po_in.currency or "USD",
        notes=po_in.notes
    )
    db.add(po)
    db.flush()

    for line_in in po_in.lines:
        if abs(line_in.quantity * line_in.unit_price - line_in.amount) > Decimal('0.0001'):
            raise HTTPException(status_code=400, detail="Line amount must exactly equal quantity * unit_price")

        line = PurchaseOrderLine(
            tenant_id=tenant_id,
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

@router.get("/", response_model=List[PurchaseOrderResponse])
def get_purchase_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    return db.query(PurchaseOrder).filter(PurchaseOrder.tenant_id == tenant_id).order_by(PurchaseOrder.created_at.desc()).all()

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
    return {"status": "success", "message": "Purchase order issued"}

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
    return {"status": "success", "message": "Purchase order cancelled"}
