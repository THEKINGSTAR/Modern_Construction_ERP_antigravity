import pytest
import uuid
from decimal import Decimal
from datetime import date

from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.models.user import User
from app.models.suppliers import Supplier
from app.models.clients import Client
from app.models.projects import Project
from app.models.warehouses import Warehouse
from app.models.materials import Material
from app.models.purchase_orders import PurchaseOrder, POStatus
from app.core.repository import BaseRepository
from app.core.context import set_current_tenant_id
from app.core.security import get_password_hash, create_access_token


def test_tenant_isolation_at_repository_layer(db_session):
    # 1. Create two tenants
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    
    t_a = Tenant(id=tenant_a_id, name="Tenant A")
    t_b = Tenant(id=tenant_b_id, name="Tenant B")
    db_session.add_all([t_a, t_b])
    db_session.commit()

    # 2. Set context to Tenant A and create a Legal Entity
    set_current_tenant_id(tenant_a_id)
    repo_le = BaseRepository(LegalEntity, db_session)
    le_a = repo_le.create({"name": "Legal Entity A", "tax_id": "123"})
    
    # Verify Tenant A can read it
    assert repo_le.get(le_a.id) is not None
    assert len(repo_le.get_all()) == 1

    # 3. Switch context to Tenant B
    set_current_tenant_id(tenant_b_id)
    repo_le_b = BaseRepository(LegalEntity, db_session)
    
    # Verify Tenant B CANNOT read Tenant A's Legal Entity
    assert repo_le_b.get(le_a.id) is None
    assert len(repo_le_b.get_all()) == 0

    # Verify Tenant B CANNOT update Tenant A's Legal Entity
    with pytest.raises(ValueError, match="Cannot update record belonging to another tenant"):
        repo_le_b.update(le_a, {"name": "Hacked Entity"})


def test_missing_tenant_context_blocks_creation(db_session):
    # Clear tenant context
    set_current_tenant_id(None)
    repo_le = BaseRepository(LegalEntity, db_session)
    
    with pytest.raises(ValueError, match="Tenant context is required for creation"):
        repo_le.create({"name": "Orphan Entity"})


def test_missing_tenant_context_blocks_reads(db_session):
    # Clear tenant context
    set_current_tenant_id(None)
    repo_le = BaseRepository(LegalEntity, db_session)
    
    with pytest.raises(ValueError, match="Tenant context is required for this operation"):
        repo_le.get_all()


def _create_tenant_and_headers(db_session):
    t_id = uuid.uuid4()
    t = Tenant(id=t_id, name=f"Tenant-{t_id.hex[:6]}")
    db_session.add(t)
    db_session.flush()

    u_id = uuid.uuid4()
    u = User(
        id=u_id,
        email=f"user_{u_id.hex[:6]}@example.com",
        hashed_password=get_password_hash("pass"),
        tenant_id=t_id,
        is_superuser=True
    )
    db_session.add(u)
    db_session.commit()

    token = create_access_token({"sub": str(u.id)})
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(t_id)
    }
    return t, u, headers


def test_negative_cross_tenant_purchase_order_blocked(client, db_session):
    """Assert Tenant B cannot create a PO referencing Tenant A's project."""
    tenant_a, user_a, headers_a = _create_tenant_and_headers(db_session)
    tenant_b, user_b, headers_b = _create_tenant_and_headers(db_session)

    # Tenant A owns this project
    proj_a = Project(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        project_number=f"PRJ-A-{uuid.uuid4().hex[:4]}",
        name="Tenant A Tower",
        status="ACTIVE"
    )
    # Tenant B owns this supplier
    supp_b = Supplier(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Tenant B Supplier"
    )
    db_session.add_all([proj_a, supp_b])
    db_session.commit()

    # Tenant B tries to create a PO on Tenant A's project
    payload = {
        "po_number": f"PO-ATTACK-{uuid.uuid4().hex[:4]}",
        "project_id": str(proj_a.id),
        "supplier_id": str(supp_b.id),
        "lines": [
            {
                "item_description": "Cross-tenant project test line",
                "unit": "PCS",
                "quantity": 10,
                "unit_price": 50.0,
                "amount": 500.0
            }
        ]
    }
    response = client.post("/api/v1/purchase-orders/", json=payload, headers=headers_b)
    assert response.status_code == 400
    assert "access denied" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


def test_negative_cross_tenant_ap_invoice_blocked(client, db_session):
    """Assert Tenant B cannot create an AP invoice referencing Tenant A's supplier."""
    tenant_a, user_a, headers_a = _create_tenant_and_headers(db_session)
    tenant_b, user_b, headers_b = _create_tenant_and_headers(db_session)

    supp_a = Supplier(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Tenant A Steel Co"
    )
    db_session.add(supp_a)
    db_session.commit()

    payload = {
        "supplier_id": str(supp_a.id),
        "number": f"INV-AP-{uuid.uuid4().hex[:4]}",
        "date": str(date.today()),
        "due_date": str(date.today()),
        "currency": "USD",
        "tax_amount": 0.0,
        "lines": [
            {
                "description": "Cross tenant AP injection",
                "quantity": 1,
                "unit_price": 1000.0
            }
        ]
    }
    response = client.post("/api/v1/ap/invoices", json=payload, headers=headers_b)
    assert response.status_code in [400, 404]
    assert "access denied" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


def test_negative_cross_tenant_ar_invoice_blocked(client, db_session):
    """Assert Tenant B cannot create an AR invoice referencing Tenant A's client."""
    tenant_a, user_a, headers_a = _create_tenant_and_headers(db_session)
    tenant_b, user_b, headers_b = _create_tenant_and_headers(db_session)

    client_a = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        name="Tenant A Real Estate Corp",
        status="ACTIVE"
    )
    db_session.add(client_a)
    db_session.commit()

    payload = {
        "client_id": str(client_a.id),
        "number": f"INV-AR-{uuid.uuid4().hex[:4]}",
        "date": str(date.today()),
        "due_date": str(date.today()),
        "currency": "USD",
        "subtotal": 2500.0,
        "tax_amount": 0.0,
        "retention_amount": 0.0,
        "total_amount": 2500.0,
        "lines": [
            {
                "description": "Cross tenant AR injection",
                "quantity": 1,
                "unit_price": 2500.0,
                "line_total": 2500.0
            }
        ]
    }
    response = client.post("/api/v1/ar/invoices", json=payload, headers=headers_b)
    assert response.status_code == 400
    assert "access denied" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()


def test_negative_cross_tenant_goods_receipt_blocked(client, db_session):
    """Assert Tenant B cannot create a goods receipt referencing Tenant A's warehouse."""
    tenant_a, user_a, headers_a = _create_tenant_and_headers(db_session)
    tenant_b, user_b, headers_b = _create_tenant_and_headers(db_session)

    wh_a = Warehouse(
        id=uuid.uuid4(),
        tenant_id=tenant_a.id,
        code=f"WH-A-{uuid.uuid4().hex[:4]}",
        name="Tenant A Central Yard"
    )
    supp_b = Supplier(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        name="Tenant B Supplier"
    )
    po_b = PurchaseOrder(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        po_number=f"PO-B-{uuid.uuid4().hex[:4]}",
        supplier_id=supp_b.id,
        status=POStatus.ISSUED
    )
    mat_b = Material(
        id=uuid.uuid4(),
        tenant_id=tenant_b.id,
        material_code=f"MAT-B-{uuid.uuid4().hex[:4]}",
        name="Steel Bar",
        base_unit="KG"
    )
    db_session.add_all([wh_a, supp_b, po_b, mat_b])
    db_session.commit()

    payload = {
        "receipt_number": f"GRN-ATTACK-{uuid.uuid4().hex[:4]}",
        "warehouse_id": str(wh_a.id),
        "supplier_id": str(supp_b.id),
        "purchase_order_id": str(po_b.id),
        "date": str(date.today()),
        "lines": [
            {
                "material_id": str(mat_b.id),
                "received_quantity": 10,
                "accepted_quantity": 10,
                "unit_cost": 25.0
            }
        ]
    }
    response = client.post("/api/v1/inventory/goods-receipts", json=payload, headers=headers_b)
    assert response.status_code == 404
    assert "access denied" in response.json()["detail"].lower() or "not found" in response.json()["detail"].lower()
