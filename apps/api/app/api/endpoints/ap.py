from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.ap_ar import APInvoice, Payment, PaymentType, InvoiceStatus
from app.models.bank import BankAccount
from app.schemas.ap_ar import (
    APInvoiceCreate, APInvoiceResponse,
    PaymentCreate, PaymentResponse,
    ThreeWayMatchResponse, APSummaryResponse
)
from app.schemas.bank import BankAccountCreate, BankAccountResponse
from app.services.ap_service import APService
from app.services.bank_service import BankService

router = APIRouter()

@router.get("/summary", response_model=APSummaryResponse)
def get_ap_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.get_ap_summary()

@router.get("/invoices", response_model=List[APInvoiceResponse])
def get_invoices(
    supplier_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    matching_status: Optional[str] = Query(None),
    purchase_order_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(APInvoice).filter(APInvoice.tenant_id == current_user.tenant_id)
    if supplier_id:
        query = query.filter(APInvoice.supplier_id == supplier_id)
    if status:
        query = query.filter(APInvoice.status == status)
    if matching_status:
        query = query.filter(APInvoice.matching_status == matching_status)
    if purchase_order_id:
        query = query.filter(APInvoice.purchase_order_id == purchase_order_id)
    
    return query.order_by(APInvoice.date.desc()).all()

@router.get("/invoices/{invoice_id}", response_model=APInvoiceResponse)
def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    invoice = db.query(APInvoice).filter(
        APInvoice.id == invoice_id,
        APInvoice.tenant_id == current_user.tenant_id
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/invoices", response_model=APInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice: APInvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.create_invoice(invoice)

@router.post("/invoices/{invoice_id}/match", response_model=ThreeWayMatchResponse)
def perform_three_way_match(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.perform_three_way_match(invoice_id)

@router.post("/invoices/{invoice_id}/approve", response_model=APInvoiceResponse)
def approve_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.approve_invoice(invoice_id)

@router.post("/invoices/{invoice_id}/post", response_model=APInvoiceResponse)
def post_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.post_invoice(invoice_id)

@router.get("/payments", response_model=List[PaymentResponse])
def get_payments(
    supplier_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Payment).filter(
        Payment.tenant_id == current_user.tenant_id,
        Payment.payment_type == PaymentType.AP_PAYMENT
    )
    if supplier_id:
        query = query.filter(Payment.supplier_id == supplier_id)
    return query.order_by(Payment.date.desc()).all()

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.tenant_id == current_user.tenant_id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    payment: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = APService(db, current_user.tenant_id, current_user.id)
    return service.create_payment(payment)

@router.get("/bank-accounts", response_model=List[BankAccountResponse])
def get_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(BankAccount).filter(BankAccount.tenant_id == current_user.tenant_id).all()

@router.post("/bank-accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_bank_account(
    account: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = BankService(db, current_user.tenant_id, current_user.id)
    return service.create_bank_account(account)
