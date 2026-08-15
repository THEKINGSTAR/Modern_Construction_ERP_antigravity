from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.commercial import (
    SubcontractCreate, SubcontractResponse,
    ClientChangeOrderCreate, ClientChangeOrderResponse,
    SubcontractPaymentApplicationCreate, SubcontractPaymentApplicationResponse,
    ClientPaymentApplicationCreate, ClientPaymentApplicationResponse
)
from app.services.commercial_service import CommercialService
from app.core.exceptions import BaseAPIException

router = APIRouter()

@router.post("/subcontracts", response_model=SubcontractResponse, status_code=201)
def create_subcontract(
    subcontract_in: SubcontractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.create_subcontract(current_user.tenant_id, current_user.id, subcontract_in)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/client-change-orders", response_model=ClientChangeOrderResponse, status_code=201)
def create_client_change_order(
    change_order_in: ClientChangeOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.create_client_change_order(current_user.tenant_id, current_user.id, change_order_in)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/client-change-orders/{cco_id}/approve", response_model=ClientChangeOrderResponse)
def approve_client_change_order(
    cco_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.approve_client_change_order(current_user.tenant_id, current_user.id, cco_id)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/subcontract-payment-applications", response_model=SubcontractPaymentApplicationResponse, status_code=201)
def create_subcontract_payment_app(
    app_in: SubcontractPaymentApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.create_subcontract_payment_application(current_user.tenant_id, current_user.id, app_in)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/subcontract-payment-applications/{app_id}/approve", response_model=SubcontractPaymentApplicationResponse)
def approve_subcontract_payment_app(
    app_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.approve_subcontract_payment_application(current_user.tenant_id, current_user.id, app_id)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/subcontract-payment-applications/{app_id}/post", response_model=SubcontractPaymentApplicationResponse)
def post_subcontract_payment_app(
    app_id: UUID,
    wip_account_id: UUID,
    ap_account_id: UUID,
    retention_account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.post_subcontract_payment_application(
            current_user.tenant_id, 
            current_user.id, 
            app_id, 
            wip_account_id, 
            ap_account_id, 
            retention_account_id
        )
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/client-payment-applications", response_model=ClientPaymentApplicationResponse, status_code=201)
def create_client_payment_app(
    app_in: ClientPaymentApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.create_client_payment_application(current_user.tenant_id, current_user.id, app_in)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/client-payment-applications/{app_id}/approve", response_model=ClientPaymentApplicationResponse)
def approve_client_payment_app(
    app_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.approve_client_payment_application(current_user.tenant_id, current_user.id, app_id)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/client-payment-applications/{app_id}/post", response_model=ClientPaymentApplicationResponse)
def post_client_payment_app(
    app_id: UUID,
    ar_account_id: UUID,
    revenue_account_id: UUID,
    retention_account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.post_client_payment_application(
            current_user.tenant_id, 
            current_user.id, 
            app_id, 
            ar_account_id, 
            revenue_account_id, 
            retention_account_id
        )
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
