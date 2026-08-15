from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.ap_ar import APInvoiceCreate, APInvoiceResponse, PaymentCreate, PaymentResponse
from app.services.ap_service import APService
from app.models.tenant import Tenant

router = APIRouter()

@router.post("/invoices", response_model=APInvoiceResponse, status_code=201)
def create_invoice(
    invoice: APInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.create_invoice(invoice)

@router.post("/invoices/{invoice_id}/post", response_model=APInvoiceResponse)
def post_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.post_invoice(invoice_id)

@router.post("/payments", response_model=PaymentResponse, status_code=201)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.create_payment(payment)
