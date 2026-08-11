import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.inventory import InventoryTransaction, InventoryBalance, TransactionType
from app.models.org_settings import TenantSettings

class InventoryService:
    def __init__(self, db: Session, tenant_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _get_or_create_balance_for_update(self, warehouse_id: uuid.UUID, material_id: uuid.UUID) -> InventoryBalance:
        balance = self.db.query(InventoryBalance).filter(
            InventoryBalance.tenant_id == self.tenant_id,
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.material_id == material_id
        ).with_for_update().first()

        if not balance:
            balance = InventoryBalance(
                tenant_id=self.tenant_id,
                warehouse_id=warehouse_id,
                material_id=material_id,
                quantity=Decimal("0.0000"),
                total_cost=Decimal("0.0000")
            )
            self.db.add(balance)
            self.db.flush() # flush to get it in the session
            # Re-fetch with lock just to be safe if another transaction created it
            balance = self.db.query(InventoryBalance).filter(
                InventoryBalance.tenant_id == self.tenant_id,
                InventoryBalance.warehouse_id == warehouse_id,
                InventoryBalance.material_id == material_id
            ).with_for_update().first()

        return balance

    def _get_current_wac(self, balance: InventoryBalance) -> Decimal:
        if balance.quantity > 0:
            return balance.total_cost / balance.quantity
        return Decimal("0.0000")

    def post_in_transaction(self, 
                            warehouse_id: uuid.UUID, 
                            material_id: uuid.UUID, 
                            transaction_type: TransactionType, 
                            quantity: Decimal, 
                            unit_cost: Decimal, 
                            reference_type: Optional[str] = None, 
                            reference_id: Optional[uuid.UUID] = None,
                            project_id: Optional[uuid.UUID] = None) -> InventoryTransaction:
        if quantity <= 0:
            raise ValueError("IN transaction quantity must be positive")
        
        balance = self._get_or_create_balance_for_update(warehouse_id, material_id)
        
        total_cost = quantity * unit_cost
        
        # Create transaction
        txn = InventoryTransaction(
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            material_id=material_id,
            project_id=project_id,
            transaction_type=transaction_type,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            reference_type=reference_type,
            reference_id=reference_id
        )
        self.db.add(txn)
        
        # Update balance (WAC is naturally updated by adding value and qty)
        balance.quantity += quantity
        balance.total_cost += total_cost
        
        return txn

    def post_out_transaction(self, 
                             warehouse_id: uuid.UUID, 
                             material_id: uuid.UUID, 
                             transaction_type: TransactionType, 
                             quantity: Decimal, 
                             reference_type: Optional[str] = None, 
                             reference_id: Optional[uuid.UUID] = None,
                             project_id: Optional[uuid.UUID] = None) -> InventoryTransaction:
        if quantity <= 0:
            raise ValueError("OUT transaction quantity must be positive")
            
        balance = self._get_or_create_balance_for_update(warehouse_id, material_id)
        
        if balance.quantity < quantity:
            # Check tenant setting for negative stock
            settings = self.db.query(TenantSettings).filter_by(tenant_id=self.tenant_id).first()
            # For MVP, we do not allow negative stock unless explicitly configured (assuming not for now)
            raise HTTPException(status_code=400, detail=f"Insufficient stock for material {material_id} in warehouse {warehouse_id}. Available: {balance.quantity}, Requested: {quantity}")

        unit_cost = self._get_current_wac(balance)
        total_cost = quantity * unit_cost
        
        # Create transaction
        txn = InventoryTransaction(
            tenant_id=self.tenant_id,
            warehouse_id=warehouse_id,
            material_id=material_id,
            project_id=project_id,
            transaction_type=transaction_type,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            reference_type=reference_type,
            reference_id=reference_id
        )
        self.db.add(txn)
        
        # Update balance
        balance.quantity -= quantity
        balance.total_cost -= total_cost
        
        return txn

    def post_transfer(self,
                      source_warehouse_id: uuid.UUID,
                      destination_warehouse_id: uuid.UUID,
                      material_id: uuid.UUID,
                      quantity: Decimal,
                      reference_type: Optional[str] = None,
                      reference_id: Optional[uuid.UUID] = None) -> tuple[InventoryTransaction, InventoryTransaction]:
        
        # Post OUT from source (this gets the current WAC)
        out_txn = self.post_out_transaction(
            warehouse_id=source_warehouse_id,
            material_id=material_id,
            transaction_type=TransactionType.TRANSFER_OUT,
            quantity=quantity,
            reference_type=reference_type,
            reference_id=reference_id
        )
        
        # Post IN to destination using the WAC from the source warehouse
        in_txn = self.post_in_transaction(
            warehouse_id=destination_warehouse_id,
            material_id=material_id,
            transaction_type=TransactionType.TRANSFER_IN,
            quantity=quantity,
            unit_cost=out_txn.unit_cost,
            reference_type=reference_type,
            reference_id=reference_id
        )
        
        return out_txn, in_txn
