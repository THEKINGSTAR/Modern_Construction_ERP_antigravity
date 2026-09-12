from typing import List, Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.ap_ar import (
    ARInvoiceCreate,
    ARInvoiceResponse,
    PaymentCreate,
    PaymentResponse,
    ARSummaryResponse
)
from app.services.ar_service import ARService

router = APIRouter()


@router.get("/summary", response_model=ARSummaryResponse)
def get_ar_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.get_ar_summary()


@router.get("/invoices", response_model=List[ARInvoiceResponse])
def list_invoices(
    client_id: Optional[UUID] = Query(None),
    contract_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.list_invoices(
        client_id=client_id,
        contract_id=contract_id,
        status=status,
        search=search,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/invoices/{invoice_id}", response_model=ARInvoiceResponse)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.get_invoice(invoice_id)


@router.post("/invoices", response_model=ARInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice: ARInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.create_invoice(invoice)


@router.post("/invoices/from-payment-application/{payment_app_id}", response_model=ARInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice_from_payment_application(
    payment_app_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.create_invoice_from_payment_application(payment_app_id)


@router.post("/invoices/{invoice_id}/approve", response_model=ARInvoiceResponse)
def approve_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.approve_invoice(invoice_id)


@router.post("/invoices/{invoice_id}/post", response_model=ARInvoiceResponse)
def post_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.post_invoice(invoice_id)


@router.get("/receipts", response_model=List[PaymentResponse])
def list_receipts(
    client_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.list_receipts(client_id=client_id, search=search)


@router.get("/receipts/{receipt_id}", response_model=PaymentResponse)
def get_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.get_receipt(receipt_id)


@router.post("/receipts", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_receipt(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ARService(db, current_user.tenant_id, current_user.id)
    return service.create_receipt(payment)
