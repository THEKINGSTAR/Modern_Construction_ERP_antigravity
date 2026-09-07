from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.commercial import (
    SubcontractCreate, SubcontractResponse,
    ClientChangeOrderCreate, ClientChangeOrderResponse,
    SubcontractChangeOrderCreate, SubcontractChangeOrderResponse,
    SubcontractPaymentApplicationCreate, SubcontractPaymentApplicationResponse,
    ClientPaymentApplicationCreate, ClientPaymentApplicationResponse,
    CommercialSummaryResponse
)
from app.services.commercial_service import CommercialService
from app.core.exceptions import BaseAPIException

router = APIRouter()

# --- Summary ---
@router.get("/summary", response_model=CommercialSummaryResponse)
def get_commercial_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_commercial_summary(current_user.tenant_id)

# --- Subcontracts ---
@router.get("/subcontracts", response_model=List[SubcontractResponse])
def get_subcontracts(
    project_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_subcontracts(current_user.tenant_id, project_id)

@router.get("/subcontracts/{subcontract_id}", response_model=SubcontractResponse)
def get_subcontract(
    subcontract_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    sc = service.get_subcontract(current_user.tenant_id, subcontract_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Subcontract not found")
    return sc

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

# --- Client Change Orders ---
@router.get("/client-change-orders", response_model=List[ClientChangeOrderResponse])
def get_client_change_orders(
    contract_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_client_change_orders(current_user.tenant_id, contract_id)

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

# --- Subcontract Change Orders ---
@router.get("/subcontract-change-orders", response_model=List[SubcontractChangeOrderResponse])
def get_subcontract_change_orders(
    subcontract_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_subcontract_change_orders(current_user.tenant_id, subcontract_id)

@router.post("/subcontract-change-orders", response_model=SubcontractChangeOrderResponse, status_code=201)
def create_subcontract_change_order(
    change_order_in: SubcontractChangeOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.create_subcontract_change_order(current_user.tenant_id, current_user.id, change_order_in)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/subcontract-change-orders/{sco_id}/approve", response_model=SubcontractChangeOrderResponse)
def approve_subcontract_change_order(
    sco_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    try:
        return service.approve_subcontract_change_order(current_user.tenant_id, current_user.id, sco_id)
    except BaseAPIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

# --- Subcontract Payment Applications ---
@router.get("/subcontract-payment-applications", response_model=List[SubcontractPaymentApplicationResponse])
def get_subcontract_payment_applications(
    subcontract_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_subcontract_payment_applications(current_user.tenant_id, subcontract_id)

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
    wip_account_id: UUID = Query(...),
    ap_account_id: UUID = Query(...),
    retention_account_id: UUID = Query(...),
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

# --- Client Payment Applications ---
@router.get("/client-payment-applications", response_model=List[ClientPaymentApplicationResponse])
def get_client_payment_applications(
    contract_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = CommercialService(db)
    return service.get_client_payment_applications(current_user.tenant_id, contract_id)

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
    ar_account_id: UUID = Query(...),
    revenue_account_id: UUID = Query(...),
    retention_account_id: UUID = Query(...),
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
