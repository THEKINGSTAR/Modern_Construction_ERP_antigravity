from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.requisitions import PurchaseRequisition, PurchaseRequisitionLine, PRStatus
from app.schemas.requisitions import PurchaseRequisitionCreate, PurchaseRequisitionResponse

router = APIRouter()

@router.post("/", response_model=PurchaseRequisitionResponse, status_code=status.HTTP_201_CREATED)
def create_requisition(
    req_in: PurchaseRequisitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    pr = PurchaseRequisition(
        pr_number=req_in.pr_number,
        project_id=req_in.project_id,
        requester_id=req_in.requester_id,
        description=req_in.description,
        status=PRStatus.DRAFT,
        required_date=req_in.required_date
    )
    db.add(pr)
    db.flush()

    for line_in in req_in.lines:
        line = PurchaseRequisitionLine(
            requisition_id=pr.id,
            cost_code_id=line_in.cost_code_id,
            item_description=line_in.item_description,
            unit=line_in.unit,
            quantity=line_in.quantity
        )
        db.add(line)
    
    db.commit()
    db.refresh(pr)
    return pr

@router.get("/{pr_id}", response_model=PurchaseRequisitionResponse)
def get_requisition(
    pr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    pr = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == pr_id, PurchaseRequisition.tenant_id == tenant_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return pr

@router.post("/{pr_id}/submit")
def submit_requisition(
    pr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    pr = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == pr_id, PurchaseRequisition.tenant_id == tenant_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if pr.status != PRStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT requisitions can be submitted")
    
    pr.status = PRStatus.SUBMITTED
    db.commit()
    return {"status": "success", "message": "Requisition submitted"}

@router.post("/{pr_id}/approve")
def approve_requisition(
    pr_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    pr = db.query(PurchaseRequisition).filter(PurchaseRequisition.id == pr_id, PurchaseRequisition.tenant_id == tenant_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="Requisition not found")
    if pr.status != PRStatus.SUBMITTED:
        raise HTTPException(status_code=400, detail="Only SUBMITTED requisitions can be approved")
    
    pr.status = PRStatus.APPROVED
    db.commit()
    return {"status": "success", "message": "Requisition approved"}
