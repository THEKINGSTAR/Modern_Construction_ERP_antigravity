from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.rfqs import RFQ, RFQLine, RFQStatus
from app.models.requisitions import PurchaseRequisition, PRStatus
from app.schemas.rfqs import RFQCreate, RFQResponse

router = APIRouter()

@router.post("/", response_model=RFQResponse, status_code=status.HTTP_201_CREATED)
def create_rfq(
    rfq_in: RFQCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    if rfq_in.requisition_id:
        pr = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == rfq_in.requisition_id).first()
        if not pr or pr.status != PRStatus.APPROVED:
            raise HTTPException(status_code=400, detail="Linked PR must be APPROVED")

    rfq = RFQ(
        rfq_number=rfq_in.rfq_number,
        project_id=rfq_in.project_id,
        requisition_id=rfq_in.requisition_id,
        title=rfq_in.title,
        description=rfq_in.description,
        status=RFQStatus.DRAFT,
        due_date=rfq_in.due_date
    )
    db.add(rfq)
    db.flush()

    for line_in in rfq_in.lines:
        line = RFQLine(
            rfq_id=rfq.id,
            pr_line_id=line_in.pr_line_id,
            item_description=line_in.item_description,
            unit=line_in.unit,
            quantity=line_in.quantity
        )
        db.add(line)
    
    db.commit()
    db.refresh(rfq)
    return rfq

@router.get("/{rfq_id}", response_model=RFQResponse)
def get_rfq(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    return rfq

@router.post("/{rfq_id}/publish")
def publish_rfq(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status != RFQStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT RFQs can be published")
    
    rfq.status = RFQStatus.PUBLISHED
    db.commit()
    return {"status": "success"}

@router.post("/{rfq_id}/close")
def close_rfq(
    rfq_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id, RFQ.tenant_id == tenant_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="RFQ not found")
    if rfq.status != RFQStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Only PUBLISHED RFQs can be closed")
    
    rfq.status = RFQStatus.CLOSED
    db.commit()
    return {"status": "success"}
