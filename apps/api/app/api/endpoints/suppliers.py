from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.suppliers import Supplier, SupplierContact
from app.schemas.suppliers import SupplierCreate, SupplierResponse

router = APIRouter()

@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    supplier = Supplier(
        tenant_id=tenant_id,
        name=supplier_in.name,
        legal_name=supplier_in.legal_name,
        tax_identifier=supplier_in.tax_identifier,
        address=supplier_in.address,
        status=supplier_in.status,
    )
    db.add(supplier)
    db.flush()

    for contact_in in supplier_in.contacts:
        contact = SupplierContact(
            tenant_id=tenant_id,
            supplier_id=supplier.id,
            name=contact_in.name,
            email=contact_in.email,
            phone=contact_in.phone,
            role=contact_in.role
        )
        db.add(contact)
    
    db.commit()
    db.refresh(supplier)
    return supplier

@router.get("/", response_model=List[SupplierResponse])
def get_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    return db.query(Supplier).filter(Supplier.tenant_id == tenant_id).order_by(Supplier.name.asc()).all()

@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.tenant_id == tenant_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier
