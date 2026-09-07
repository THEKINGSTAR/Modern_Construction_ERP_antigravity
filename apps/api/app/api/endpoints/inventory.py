from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_tenant
from app.models.user import User
from app.schemas.inventory import (
    GoodsReceiptCreate, GoodsReceiptResponse, GoodsReceiptDetailResponse,
    MaterialIssueCreate, MaterialIssueResponse, MaterialIssueDetailResponse,
    InventoryBalanceResponse, InventoryBalanceDetailResponse,
    InventoryTransferCreate, InventoryTransferResponse, InventoryTransferDetailResponse,
    InventoryAdjustmentCreate, InventoryAdjustmentResponse,
    MaterialResponse, MaterialCreate,
    WarehouseResponse, WarehouseCreate,
    InventoryTransactionResponse,
    InventorySummaryResponse
)
from app.models.inventory import TransactionType, InventoryBalance, InventoryTransaction
from app.models.goods_receipts import GoodsReceipt, GoodsReceiptLine, GoodsReceiptStatus
from app.models.material_issues import MaterialIssue, MaterialIssueLine, MaterialIssueStatus
from app.models.inventory_transfers import InventoryTransfer, InventoryTransferLine, InventoryTransferStatus
from app.models.inventory_adjustments import InventoryAdjustment, InventoryAdjustmentLine, InventoryAdjustmentStatus, AdjustmentType
from app.models.materials import Material
from app.models.warehouses import Warehouse
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine
from app.services.inventory import InventoryService

router = APIRouter(tags=["Inventory"])

@router.get("/summary", response_model=InventorySummaryResponse)
def get_inventory_summary(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    # Total valuation and total stock quantity
    val_row = db.query(
        func.coalesce(func.sum(InventoryBalance.total_cost), 0).label("total_val"),
        func.coalesce(func.sum(InventoryBalance.quantity), 0).label("total_qty")
    ).filter(InventoryBalance.tenant_id == tenant_id).first()

    total_valuation = Decimal(str(val_row.total_val if val_row else 0))
    total_stock_quantity = Decimal(str(val_row.total_qty if val_row else 0))

    total_items = db.query(Material).filter(Material.tenant_id == tenant_id, Material.active == True).count()
    total_warehouses = db.query(Warehouse).filter(Warehouse.tenant_id == tenant_id).count()
    total_receipts = db.query(GoodsReceipt).filter(GoodsReceipt.tenant_id == tenant_id).count()
    total_issues = db.query(MaterialIssue).filter(MaterialIssue.tenant_id == tenant_id).count()
    total_transfers = db.query(InventoryTransfer).filter(InventoryTransfer.tenant_id == tenant_id).count()

    recent_txns = db.query(InventoryTransaction).filter(
        InventoryTransaction.tenant_id == tenant_id
    ).order_by(InventoryTransaction.transaction_date.desc()).limit(10).all()

    # Top materials by valuation
    top_bal_records = db.query(
        InventoryBalance.id,
        InventoryBalance.warehouse_id,
        Warehouse.name.label("warehouse_name"),
        InventoryBalance.material_id,
        Material.material_code,
        Material.name.label("material_name"),
        Material.base_unit,
        InventoryBalance.quantity,
        InventoryBalance.total_cost
    ).join(
        Warehouse, Warehouse.id == InventoryBalance.warehouse_id
    ).join(
        Material, Material.id == InventoryBalance.material_id
    ).filter(
        InventoryBalance.tenant_id == tenant_id
    ).order_by(InventoryBalance.total_cost.desc()).limit(8).all()

    top_materials = []
    for b in top_bal_records:
        unit_c = (b.total_cost / b.quantity) if b.quantity > 0 else Decimal(0)
        top_materials.append(InventoryBalanceDetailResponse(
            id=b.id,
            warehouse_id=b.warehouse_id,
            warehouse_name=b.warehouse_name,
            material_id=b.material_id,
            material_code=b.material_code,
            material_name=b.material_name,
            base_unit=b.base_unit,
            quantity=b.quantity,
            unit_cost=unit_c,
            total_cost=b.total_cost
        ))

    return InventorySummaryResponse(
        total_valuation=total_valuation,
        total_stock_quantity=total_stock_quantity,
        total_items_count=total_items,
        total_warehouses_count=total_warehouses,
        total_receipts_count=total_receipts,
        total_issues_count=total_issues,
        total_transfers_count=total_transfers,
        recent_transactions=recent_txns,
        top_materials=top_materials
    )


@router.get("/goods-receipts", response_model=List[GoodsReceiptDetailResponse])
def get_goods_receipts(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(GoodsReceipt).filter(
        GoodsReceipt.tenant_id == tenant_id
    ).order_by(GoodsReceipt.date.desc()).all()


@router.get("/goods-receipts/{receipt_id}", response_model=GoodsReceiptDetailResponse)
def get_goods_receipt(
    receipt_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    rcpt = db.query(GoodsReceipt).filter(
        GoodsReceipt.id == receipt_id,
        GoodsReceipt.tenant_id == tenant_id
    ).first()
    if not rcpt:
        raise HTTPException(status_code=404, detail="Goods receipt not found")
    return rcpt


@router.post("/goods-receipts", response_model=GoodsReceiptDetailResponse)
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
        status=GoodsReceiptStatus.POSTED
    )
    db.add(db_receipt)
    db.flush()

    service = InventoryService(db, tenant_id)

    # 2. Add Lines and Post Inventory
    for line in receipt.lines:
        po_line_id = line.purchase_order_line_id
        if not po_line_id:
            po_line = db.query(PurchaseOrderLine).filter(
                PurchaseOrderLine.purchase_order_id == receipt.purchase_order_id,
                PurchaseOrderLine.tenant_id == tenant_id
            ).first()
            if po_line:
                po_line_id = po_line.id
            else:
                raise HTTPException(status_code=400, detail="Cannot find valid purchase order line for receipt")

        db_line = GoodsReceiptLine(
            tenant_id=tenant_id,
            goods_receipt_id=db_receipt.id,
            purchase_order_line_id=po_line_id,
            material_id=line.material_id,
            received_quantity=line.received_quantity,
            accepted_quantity=line.accepted_quantity,
            rejected_quantity=line.rejected_quantity,
            unit_cost=line.unit_cost,
            notes=line.notes
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


@router.get("/material-issues", response_model=List[MaterialIssueDetailResponse])
def get_material_issues(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(MaterialIssue).filter(
        MaterialIssue.tenant_id == tenant_id
    ).order_by(MaterialIssue.date.desc()).all()


@router.get("/material-issues/{issue_id}", response_model=MaterialIssueDetailResponse)
def get_material_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    iss = db.query(MaterialIssue).filter(
        MaterialIssue.id == issue_id,
        MaterialIssue.tenant_id == tenant_id
    ).first()
    if not iss:
        raise HTTPException(status_code=404, detail="Material issue not found")
    return iss


@router.post("/material-issues", response_model=MaterialIssueDetailResponse)
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
        requested_by_id=issue.requested_by_id or current_user.id,
        status=MaterialIssueStatus.POSTED
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
                unit_cost=txn.unit_cost,
                notes=line.notes
            )
            db.add(db_line)

    db.commit()
    db.refresh(db_issue)
    return db_issue


@router.get("/transfers", response_model=List[InventoryTransferDetailResponse])
def get_inventory_transfers(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(InventoryTransfer).filter(
        InventoryTransfer.tenant_id == tenant_id
    ).order_by(InventoryTransfer.date.desc()).all()


@router.get("/transfers/{transfer_id}", response_model=InventoryTransferDetailResponse)
def get_inventory_transfer(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    trf = db.query(InventoryTransfer).filter(
        InventoryTransfer.id == transfer_id,
        InventoryTransfer.tenant_id == tenant_id
    ).first()
    if not trf:
        raise HTTPException(status_code=404, detail="Inventory transfer not found")
    return trf


@router.post("/transfers", response_model=InventoryTransferDetailResponse)
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


@router.get("/balances", response_model=List[InventoryBalanceResponse])
def get_inventory_balances(
    warehouse_id: Optional[UUID] = None,
    material_id: Optional[UUID] = None,
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


@router.get("/balances/detail", response_model=List[InventoryBalanceDetailResponse])
def get_detailed_balances(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    balances = db.query(
        InventoryBalance.id,
        InventoryBalance.warehouse_id,
        Warehouse.name.label("warehouse_name"),
        InventoryBalance.material_id,
        Material.material_code,
        Material.name.label("material_name"),
        Material.base_unit,
        InventoryBalance.quantity,
        InventoryBalance.total_cost
    ).join(
        Warehouse, Warehouse.id == InventoryBalance.warehouse_id
    ).join(
        Material, Material.id == InventoryBalance.material_id
    ).filter(
        InventoryBalance.tenant_id == tenant_id
    ).order_by(InventoryBalance.total_cost.desc()).all()

    results = []
    for b in balances:
        unit_c = (b.total_cost / b.quantity) if b.quantity > 0 else Decimal(0)
        results.append(InventoryBalanceDetailResponse(
            id=b.id,
            warehouse_id=b.warehouse_id,
            warehouse_name=b.warehouse_name,
            material_id=b.material_id,
            material_code=b.material_code,
            material_name=b.material_name,
            base_unit=b.base_unit,
            quantity=b.quantity,
            unit_cost=unit_c,
            total_cost=b.total_cost
        ))
    return results


@router.get("/materials", response_model=List[MaterialResponse])
def get_materials(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(Material).filter(
        Material.tenant_id == tenant_id
    ).order_by(Material.material_code.asc()).all()


@router.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_in: MaterialCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    mat = Material(
        tenant_id=tenant_id,
        material_code=material_in.material_code,
        name=material_in.name,
        description=material_in.description,
        category=material_in.category,
        base_unit=material_in.base_unit,
        active=True
    )
    db.add(mat)
    db.commit()
    db.refresh(mat)
    return mat


@router.get("/warehouses", response_model=List[WarehouseResponse])
def get_warehouses(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(Warehouse).filter(
        Warehouse.tenant_id == tenant_id
    ).order_by(Warehouse.code.asc()).all()


@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(
    wh_in: WarehouseCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    wh = Warehouse(
        tenant_id=tenant_id,
        code=wh_in.code,
        name=wh_in.name,
        location=wh_in.location,
        type=wh_in.type,
        project_id=wh_in.project_id
    )
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


@router.get("/transactions", response_model=List[InventoryTransactionResponse])
def get_transactions(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user)
):
    return db.query(InventoryTransaction).filter(
        InventoryTransaction.tenant_id == tenant_id
    ).order_by(InventoryTransaction.transaction_date.desc()).all()


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
