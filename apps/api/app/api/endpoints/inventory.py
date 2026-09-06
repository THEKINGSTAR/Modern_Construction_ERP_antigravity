from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.schemas.inventory import (
    GoodsReceiptCreate, GoodsReceiptResponse,
    MaterialIssueCreate, MaterialIssueResponse,
    InventoryBalanceResponse
)
from app.models.inventory import TransactionType, InventoryBalance
from app.models.goods_receipts import GoodsReceipt, GoodsReceiptLine, GoodsReceiptStatus
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from app.services.inventory import InventoryService

router = APIRouter(tags=["Inventory"])

@router.post("/goods-receipts", response_model=GoodsReceiptResponse)
def create_goods_receipt(
    receipt: GoodsReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    # 1. Create Receipt Document
    db_receipt = GoodsReceipt(
        tenant_id=tenant_id,
        receipt_number=receipt.receipt_number,
        purchase_order_id=receipt.purchase_order_id,
        supplier_id=receipt.supplier_id,
        warehouse_id=receipt.warehouse_id,
        date=receipt.date,
        notes=receipt.notes,
        status=GoodsReceiptStatus.POSTED, # Post immediately for MVP
        created_by_id=current_user.id
    )
    db.add(db_receipt)
    db.flush()

    service = InventoryService(db, tenant_id)

    # 2. Add Lines and Post Inventory
    for line in receipt.lines:
        db_line = GoodsReceiptLine(
            tenant_id=tenant_id,
            goods_receipt_id=db_receipt.id,
            purchase_order_line_id=line.purchase_order_line_id,
            material_id=line.material_id,
            received_quantity=line.received_quantity,
            accepted_quantity=line.accepted_quantity,
            rejected_quantity=line.rejected_quantity,
            unit_cost=line.unit_cost,
            notes=line.notes,
            created_by_id=current_user.id
        )
        db.add(db_line)
        db.flush()
        
        # Post to ledger (only accepted quantity)
        if line.accepted_quantity > 0:
            service.post_in_transaction(
                warehouse_id=receipt.warehouse_id,
                material_id=line.material_id,
                transaction_type=TransactionType.RECEIPT,
                quantity=line.accepted_quantity,
                unit_cost=line.unit_cost,
                reference_type="GOODS_RECEIPT",
                reference_id=db_receipt.id
            )

    db.commit()
    db.refresh(db_receipt)
    return db_receipt


@router.post("/material-issues", response_model=MaterialIssueResponse)
def create_material_issue(
    issue: MaterialIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    # 1. Create Issue Document
    db_issue = MaterialIssue(
        tenant_id=tenant_id,
        issue_number=issue.issue_number,
        warehouse_id=issue.warehouse_id,
        project_id=issue.project_id,
        cost_code_id=issue.cost_code_id,
        date=issue.date,
        purpose=issue.purpose,
        requested_by_id=issue.requested_by_id,
        status=MaterialIssueStatus.POSTED, # Post immediately for MVP
        created_by_id=current_user.id
    )
    db.add(db_issue)
    db.flush()

    service = InventoryService(db, tenant_id)

    # 2. Add Lines and Post Inventory
    for line in issue.lines:
        if line.quantity > 0:
            txn = service.post_out_transaction(
                warehouse_id=issue.warehouse_id,
                material_id=line.material_id,
                transaction_type=TransactionType.ISSUE,
                quantity=line.quantity,
                reference_type="MATERIAL_ISSUE",
                reference_id=db_issue.id,
                project_id=issue.project_id
            )
            
            db_line = MaterialIssueLine(
                tenant_id=tenant_id,
                material_issue_id=db_issue.id,
                material_id=line.material_id,
                quantity=line.quantity,
                unit_cost=txn.unit_cost, # Derived from WAC
                notes=line.notes,
                created_by_id=current_user.id
            )
            db.add(db_line)

    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.get("/balances", response_model=List[InventoryBalanceResponse])
def get_inventory_balances(
    warehouse_id: UUID = None,
    material_id: UUID = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    query = db.query(InventoryBalance).filter(InventoryBalance.tenant_id == tenant_id)
    if warehouse_id:
        query = query.filter(InventoryBalance.warehouse_id == warehouse_id)
    if material_id:
        query = query.filter(InventoryBalance.material_id == material_id)
        
    return query.all()


from app.schemas.inventory import (
    InventoryTransferCreate, InventoryTransferResponse,
    InventoryAdjustmentCreate, InventoryAdjustmentResponse
)
from app.models.inventory_transfers import InventoryTransfer, InventoryTransferLine, InventoryTransferStatus
from app.models.inventory_adjustments import InventoryAdjustment, InventoryAdjustmentLine, InventoryAdjustmentStatus, AdjustmentType

@router.post("/transfers", response_model=InventoryTransferResponse)
def create_inventory_transfer(
    transfer: InventoryTransferCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    db_transfer = InventoryTransfer(
        tenant_id=tenant_id,
        transfer_number=transfer.transfer_number,
        source_warehouse_id=transfer.source_warehouse_id,
        destination_warehouse_id=transfer.destination_warehouse_id,
        date=transfer.date,
        notes=transfer.notes,
        status=InventoryTransferStatus.POSTED
    )
    db.add(db_transfer)
    db.flush()

    service = InventoryService(db, tenant_id)

    for line in transfer.lines:
        if line.quantity > 0:
            out_txn, in_txn = service.post_transfer(
                source_warehouse_id=transfer.source_warehouse_id,
                destination_warehouse_id=transfer.destination_warehouse_id,
                material_id=line.material_id,
                quantity=line.quantity,
                reference_type="INVENTORY_TRANSFER",
                reference_id=db_transfer.id
            )
            
            db_line = InventoryTransferLine(
                tenant_id=tenant_id,
                inventory_transfer_id=db_transfer.id,
                material_id=line.material_id,
                quantity=line.quantity,
                unit_cost=out_txn.unit_cost,
                notes=line.notes
            )
            db.add(db_line)

    db.commit()
    db.refresh(db_transfer)
    return db_transfer


@router.post("/adjustments", response_model=InventoryAdjustmentResponse)
def create_inventory_adjustment(
    adjustment: InventoryAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    tenant_id: UUID = Depends(get_current_tenant)
):
    db_adjustment = InventoryAdjustment(
        tenant_id=tenant_id,
        adjustment_number=adjustment.adjustment_number,
        warehouse_id=adjustment.warehouse_id,
        date=adjustment.date,
        reason=adjustment.reason,
        status=InventoryAdjustmentStatus.POSTED
    )
    db.add(db_adjustment)
    db.flush()

    service = InventoryService(db, tenant_id)

    for line in adjustment.lines:
        if line.quantity > 0:
            transaction_type = TransactionType.ADJUSTMENT_IN if line.adjustment_type == AdjustmentType.IN else TransactionType.ADJUSTMENT_OUT
            
            if line.adjustment_type == AdjustmentType.IN:
                service.post_in_transaction(
                    warehouse_id=adjustment.warehouse_id,
                    material_id=line.material_id,
                    transaction_type=transaction_type,
                    quantity=line.quantity,
                    unit_cost=line.unit_cost,
                    reference_type="INVENTORY_ADJUSTMENT",
                    reference_id=db_adjustment.id
                )
            else:
                service.post_out_transaction(
                    warehouse_id=adjustment.warehouse_id,
                    material_id=line.material_id,
                    transaction_type=transaction_type,
                    quantity=line.quantity,
                    reference_type="INVENTORY_ADJUSTMENT",
                    reference_id=db_adjustment.id
                )
                
            db_line = InventoryAdjustmentLine(
                tenant_id=tenant_id,
                inventory_adjustment_id=db_adjustment.id,
                material_id=line.material_id,
                adjustment_type=line.adjustment_type,
                quantity=line.quantity,
                unit_cost=line.unit_cost,
                notes=line.notes
            )
            db.add(db_line)

    db.commit()
    db.refresh(db_adjustment)
    return db_adjustment
