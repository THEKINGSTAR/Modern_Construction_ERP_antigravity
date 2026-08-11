from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import require_permissions, get_current_tenant
from app.models.boq import BOQ, BOQRevision, BOQItem
from app.schemas.boq import (
    BOQCreate, BOQResponse, BOQUpdate, 
    BOQRevisionCreate, BOQRevisionResponse, BOQRevisionWithItemsResponse,
    BOQItemCreate, BOQItemResponse, BOQItemUpdate
)

router = APIRouter()

@router.post("/", response_model=BOQResponse, status_code=status.HTTP_201_CREATED)
def create_boq(
    boq_in: BOQCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.create"]))
):
    # Create BOQ
    db_boq = BOQ(**boq_in.model_dump(), tenant_id=tenant_id)
    db.add(db_boq)
    db.flush() # flush to get id
    
    # Create initial Revision 1
    db_rev = BOQRevision(boq_id=db_boq.id, version_number=1, status="DRAFT", tenant_id=tenant_id)
    db.add(db_rev)
    db.flush()
    
    # Set current revision
    db_boq.current_revision_id = db_rev.id
    db.commit()
    db.refresh(db_boq)
    return db_boq

@router.get("/", response_model=List[BOQResponse])
def get_boqs(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.read"]))
):
    return db.query(BOQ).filter(BOQ.tenant_id == tenant_id).all()

@router.get("/{id}", response_model=BOQResponse)
def get_boq(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.read"]))
):
    boq = db.query(BOQ).filter(BOQ.id == id, BOQ.tenant_id == tenant_id).first()
    if not boq:
        raise HTTPException(status_code=404, detail="BOQ not found")
    return boq

@router.post("/{id}/revisions", response_model=BOQRevisionResponse)
def create_revision(
    id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.update"]))
):
    boq = db.query(BOQ).filter(BOQ.id == id, BOQ.tenant_id == tenant_id).first()
    if not boq:
        raise HTTPException(status_code=404, detail="BOQ not found")
        
    last_rev = db.query(BOQRevision).filter(BOQRevision.boq_id == boq.id).order_by(BOQRevision.version_number.desc()).first()
    new_version = (last_rev.version_number + 1) if last_rev else 1
    
    db_rev = BOQRevision(boq_id=boq.id, version_number=new_version, status="DRAFT", tenant_id=tenant_id)
    db.add(db_rev)
    db.flush()
    
    # Copy items if there was a previous revision
    if last_rev:
        old_items = db.query(BOQItem).filter(BOQItem.revision_id == last_rev.id).all()
        for item in old_items:
            new_item = BOQItem(
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
            
    boq.current_revision_id = db_rev.id
    db.commit()
    db.refresh(db_rev)
    return db_rev

@router.get("/revisions/{rev_id}", response_model=BOQRevisionWithItemsResponse)
def get_revision(
    rev_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.read"]))
):
    rev = db.query(BOQRevision).filter(BOQRevision.id == rev_id, BOQRevision.tenant_id == tenant_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    return rev

@router.post("/revisions/{rev_id}/items", response_model=BOQItemResponse, status_code=status.HTTP_201_CREATED)
def create_boq_item(
    rev_id: UUID,
    item_in: BOQItemCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    _ = Depends(require_permissions(["boqs.update"]))
):
    rev = db.query(BOQRevision).filter(BOQRevision.id == rev_id, BOQRevision.tenant_id == tenant_id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Revision not found")
    if rev.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Cannot modify a non-draft revision")
        
    amount = item_in.quantity * item_in.unit_rate
    db_item = BOQItem(
        **item_in.model_dump(), 
        revision_id=rev_id, 
        tenant_id=tenant_id,
        amount=amount
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
