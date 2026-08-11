from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_tenant
from app.models.estimates import Estimate, EstimateRevision, EstimateItem
from app.schemas.estimates import (
    EstimateCreate, EstimateResponse, EstimateUpdate, 
    EstimateRevisionCreate, EstimateRevisionResponse, EstimateRevisionWithItemsResponse,
    EstimateItemCreate, EstimateItemResponse, EstimateItemUpdate
)

router = APIRouter()

@router.post("/", response_model=EstimateResponse, status_code=status.HTTP_201_CREATED)
def create_estimate(
    estimate_in: EstimateCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.create"]))
):
    # Create Estimate
    db_est = Estimate(**estimate_in.model_dump(), tenant_id=tenant_id)
    db.add(db_est)
    db.flush() 
    
    # Create initial Revision 1
    db_rev = EstimateRevision(estimate_id=db_est.id, version_number=1, status="DRAFT", tenant_id=tenant_id)
    db.add(db_rev)
    db.flush()
    
    # Set current revision
    db_est.current_revision_id = db_rev.id
    db.commit()
    db.refresh(db_est)
    return db_est

@router.get("/", response_model=List[EstimateResponse])
def get_estimates(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.read"]))
):
    return db.query(Estimate).filter(Estimate.tenant_id == tenant_id).all()

@router.get("/{id}", response_model=EstimateResponse)
def get_estimate(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.read"]))
):
    est = db.query(Estimate).filter(Estimate.id == id, Estimate.tenant_id == tenant_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estimate not found")
    return est

@router.post("/{id}/revisions", response_model=EstimateRevisionResponse)
def create_revision(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.update"]))
):
    est = db.query(Estimate).filter(Estimate.id == id, Estimate.tenant_id == tenant_id).first()
    if not est:
        raise HTTPException(status_code=404, detail="Estimate not found")
        
    last_rev = db.query(EstimateRevision).filter(EstimateRevision.estimate_id == est.id).order_by(EstimateRevision.version_number.desc()).first()
    new_version = (last_rev.version_number + 1) if last_rev else 1
    
    db_rev = EstimateRevision(estimate_id=est.id, version_number=new_version, status="DRAFT", tenant_id=tenant_id)
    db.add(db_rev)
    db.flush()
    
    # Copy items if there was a previous revision
    if last_rev:
        old_items = db.query(EstimateItem).filter(EstimateItem.revision_id == last_rev.id).all()
        for item in old_items:
            new_item = EstimateItem(
                revision_id=db_rev.id,
                tenant_id=tenant_id,
                cost_code_id=item.cost_code_id,
                item_code=item.item_code,
                description=item.description,
                unit=item.unit,
                quantity=item.quantity,
                unit_rate=item.unit_rate,
                amount=item.amount
            )
            db.add(new_item)
            
    est.current_revision_id = db_rev.id
    db.commit()
    db.refresh(db_rev)
    return db_rev

@router.get("/revisions/{rev_id}", response_model=EstimateRevisionWithItemsResponse)
def get_revision(
    rev_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.read"]))
):
    rev = db.query(EstimateRevision).filter(EstimateRevision.id == rev_id, EstimateRevision.tenant_id == tenant_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    return rev

@router.post("/revisions/{rev_id}/items", response_model=EstimateItemResponse, status_code=status.HTTP_201_CREATED)
def create_estimate_item(
    rev_id: UUID,
    item_in: EstimateItemCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["estimates.update"]))
):
    rev = db.query(EstimateRevision).filter(EstimateRevision.id == rev_id, EstimateRevision.tenant_id == tenant_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    if rev.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Cannot modify a non-draft revision")
        
    amount = item_in.quantity * item_in.unit_rate
    db_item = EstimateItem(
        **item_in.model_dump(), 
        revision_id=rev_id, 
        tenant_id=tenant_id,
        amount=amount
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
