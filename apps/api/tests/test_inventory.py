import uuid
from decimal import Decimal
import pytest
from app.models.inventory import TransactionType, InventoryBalance
from app.models.materials import Material
from app.models.warehouses import Warehouse, WarehouseType
from app.models.org_settings import TenantSettings
from app.services.inventory import InventoryService

def test_wac_inventory_transactions(db_session, test_tenant):
    # Setup
    material_id = uuid.uuid4()
    material = Material(id=material_id, tenant_id=test_tenant.id, material_code="MAT-1", name="Cement", category="RAW_MATERIAL", base_unit="BAG", active=True)
    
    warehouse_id = uuid.uuid4()
    warehouse = Warehouse(id=warehouse_id, tenant_id=test_tenant.id, code="WH-1", name="Main WH", type=WarehouseType.CENTRAL)
    
    db_session.add_all([material, warehouse])
    db_session.commit()

    service = InventoryService(db_session, test_tenant.id)

    # 1. Receipt 1: 100 units @ $10 each = $1000 total. WAC = $10
    service.post_in_transaction(warehouse_id, material_id, TransactionType.RECEIPT, Decimal("100"), Decimal("10"))
    db_session.flush()
    
    balance = db_session.query(InventoryBalance).filter_by(warehouse_id=warehouse_id, material_id=material_id).first()
    assert balance.quantity == Decimal("100")
    assert balance.total_cost == Decimal("1000")

    # 2. Receipt 2: 50 units @ $16 each = $800 total. New Total = 150 units, $1800. WAC = $12
    service.post_in_transaction(warehouse_id, material_id, TransactionType.RECEIPT, Decimal("50"), Decimal("16"))
    db_session.flush()
    
    db_session.refresh(balance)
    assert balance.quantity == Decimal("150")
    assert balance.total_cost == Decimal("1800")
    assert service._get_current_wac(balance) == Decimal("12")

    # 3. Issue: 50 units @ current WAC ($12). Total cost should decrease by 50 * 12 = $600.
    txn_out = service.post_out_transaction(warehouse_id, material_id, TransactionType.ISSUE, Decimal("50"))
    db_session.flush()
    
    assert txn_out.unit_cost == Decimal("12")
    assert txn_out.total_cost == Decimal("600")
    
    db_session.refresh(balance)
    assert balance.quantity == Decimal("100")
    assert balance.total_cost == Decimal("1200") # 1800 - 600

    # 4. Try issuing more than available (should raise HTTPException)
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        service.post_out_transaction(warehouse_id, material_id, TransactionType.ISSUE, Decimal("150"))
    assert excinfo.value.status_code == 400
    assert "Insufficient stock" in excinfo.value.detail

def test_inventory_transfer(db_session, test_tenant):
    material_id = uuid.uuid4()
    material = Material(id=material_id, tenant_id=test_tenant.id, material_code="MAT-2", name="Steel", category="RAW_MATERIAL", base_unit="TON", active=True)
    
    wh1_id = uuid.uuid4()
    wh1 = Warehouse(id=wh1_id, tenant_id=test_tenant.id, code="WH-1", name="Main WH", type=WarehouseType.CENTRAL)
    
    wh2_id = uuid.uuid4()
    wh2 = Warehouse(id=wh2_id, tenant_id=test_tenant.id, code="WH-2", name="Project WH", type=WarehouseType.PROJECT)
    
    db_session.add_all([material, wh1, wh2])
    db_session.commit()

    service = InventoryService(db_session, test_tenant.id)
    
    # Receive into WH 1
    service.post_in_transaction(wh1_id, material_id, TransactionType.RECEIPT, Decimal("20"), Decimal("1000"))
    db_session.flush()
    
    # Transfer to WH 2
    out_txn, in_txn = service.post_transfer(wh1_id, wh2_id, material_id, Decimal("5"))
    db_session.flush()
    
    assert out_txn.unit_cost == Decimal("1000")
    assert in_txn.unit_cost == Decimal("1000")
    
    bal1 = db_session.query(InventoryBalance).filter_by(warehouse_id=wh1_id, material_id=material_id).first()
    bal2 = db_session.query(InventoryBalance).filter_by(warehouse_id=wh2_id, material_id=material_id).first()
    
    assert bal1.quantity == Decimal("15")
    assert bal2.quantity == Decimal("5")
