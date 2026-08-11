from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.models.quotations import SupplierQuotation, SupplierQuotationLine, QuotationStatus
from app.models.rfqs import RFQ, RFQStatus
from app.schemas.quotations import SupplierQuotationCreate, SupplierQuotationResponse

router = APIRouter()

@router.post("/", response_model=SupplierQuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    quote_in: SupplierQuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    rfq = db.query(RFQ).filter(RFQ.id == quote_in.rfq_id).first()
    if not rfq or rfq.status != RFQStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail="Can only quote against PUBLISHED RFQs")

    quote = SupplierQuotation(
        rfq_id=quote_in.rfq_id,
        supplier_id=quote_in.supplier_id,
        quotation_reference=quote_in.quotation_reference,
        status=QuotationStatus.DRAFT,
        valid_until=quote_in.valid_until,
        currency=quote_in.currency,
        notes=quote_in.notes
    )
    db.add(quote)
    db.flush()

    for line_in in quote_in.lines:
        line = SupplierQuotationLine(
            quotation_id=quote.id,
            rfq_line_id=line_in.rfq_line_id,
            unit_price=line_in.unit_price,
            quoted_quantity=line_in.quoted_quantity,
            amount=line_in.amount,
            lead_time_days=line_in.lead_time_days
        )
        db.add(line)
    
    db.commit()
    db.refresh(quote)
    return quote

@router.get("/{quote_id}", response_model=SupplierQuotationResponse)
def get_quotation(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    quote = db.query(SupplierQuotation).filter(SupplierQuotation.id == quote_id, SupplierQuotation.tenant_id == tenant_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quote

@router.post("/{quote_id}/submit")
def submit_quotation(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    quote = db.query(SupplierQuotation).filter(SupplierQuotation.id == quote_id, SupplierQuotation.tenant_id == tenant_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quote.status != QuotationStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT Quotations can be submitted")
    
    quote.status = QuotationStatus.SUBMITTED
    db.commit()
    return {"status": "success"}

@router.post("/{quote_id}/accept")
def accept_quotation(
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    quote = db.query(SupplierQuotation).filter(SupplierQuotation.id == quote_id, SupplierQuotation.tenant_id == tenant_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quote.status not in (QuotationStatus.SUBMITTED, QuotationStatus.EVALUATED):
        raise HTTPException(status_code=400, detail="Only SUBMITTED or EVALUATED Quotations can be accepted")
    
    quote.status = QuotationStatus.ACCEPTED
    db.commit()
    return {"status": "success"}
