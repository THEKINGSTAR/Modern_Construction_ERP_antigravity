import uuid
from decimal import Decimal
import threading
import concurrent.futures
from unittest.mock import patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.inventory import TransactionType, InventoryBalance
from app.models.materials import Material
from app.models.warehouses import Warehouse, WarehouseType
from app.services.inventory import InventoryService

def test_inventory_concurrency_safe_issue():
    # Setup file-based DB for concurrency
    engine = create_engine("sqlite:///test_conc.db", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db_session = SessionLocal()
    tenant_id = uuid.uuid4()
    
    from app.models.tenant import Tenant
    tenant = Tenant(id=tenant_id, name="Conc Tenant")
    db_session.add(tenant)
    db_session.commit()

    material_id = uuid.uuid4()
    material = Material(id=material_id, tenant_id=tenant_id, material_code="MAT-CONC-1", name="Sand", category="RAW_MATERIAL", base_unit="TON", active=True)
    
    warehouse_id = uuid.uuid4()
    warehouse = Warehouse(id=warehouse_id, tenant_id=tenant_id, code="WH-CONC", name="Conc WH", type=WarehouseType.CENTRAL)
    
    db_session.add_all([material, warehouse])
    db_session.commit()

    # Initial receipt of 100 units
    service = InventoryService(db_session, tenant_id)
    service.post_in_transaction(warehouse_id, material_id, TransactionType.RECEIPT, Decimal("100"), Decimal("20"))
    db_session.commit()
    db_session.close()

    # SQLite does not support true row-level locks with FOR UPDATE.
    # It will just happily let multiple transactions read 100, then all write 50.
    # To test that our logic *would* work if FOR UPDATE blocks (like in Postgres),
    # we simulate the row lock with a Python threading.Lock that is held until commit/rollback.
    row_lock = threading.Lock()
    
    def issue_stock():
        session = SessionLocal()
        
        # We'll keep track if this session holds the mock lock
        has_lock = False
        
        original_commit = session.commit
        original_rollback = session.rollback
        
        def locked_commit():
            try:
                original_commit()
            finally:
                nonlocal has_lock
                if has_lock:
                    row_lock.release()
                    has_lock = False
                    
        def locked_rollback():
            try:
                original_rollback()
            finally:
                nonlocal has_lock
                if has_lock:
                    row_lock.release()
                    has_lock = False
                    
        session.commit = locked_commit
        session.rollback = locked_rollback

        try:
            srv = InventoryService(session, tenant_id)

            original_method = srv._get_or_create_balance_for_update

            def locked_get(*args, **kwargs):
                nonlocal has_lock
                row_lock.acquire()
                has_lock = True
                return original_method(*args, **kwargs)

            srv._get_or_create_balance_for_update = locked_get

            srv.post_out_transaction(warehouse_id, material_id, TransactionType.ISSUE, Decimal("50"))
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            return False
        finally:
            session.close()

    successes = 0
    failures = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        results = [executor.submit(issue_stock) for _ in range(3)]
        for r in concurrent.futures.as_completed(results):
            if r.result():
                successes += 1
            else:
                failures += 1
                
    assert successes == 2
    assert failures == 1
    
    db_session = SessionLocal()
    balance = db_session.query(InventoryBalance).filter_by(warehouse_id=warehouse_id, material_id=material_id).first()
    assert balance.quantity == Decimal("0.0000")
    db_session.close()
    
    Base.metadata.drop_all(bind=engine)

