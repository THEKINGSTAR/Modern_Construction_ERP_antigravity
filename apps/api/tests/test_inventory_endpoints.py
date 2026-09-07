import pytest
from uuid import uuid4
from decimal import Decimal

def test_inventory_lifecycle(client, test_user, db_session, auth_headers):
    # 1. Create a project and cost code
    prj_res = client.post("/api/v1/projects/", json={
        "project_number": f"PRJ-INV-{uuid4().hex[:6].upper()}",
        "name": "Inventory Test Tower",
        "status": "ACTIVE"
    }, headers=auth_headers)
    assert prj_res.status_code == 201, prj_res.text
    project_id = prj_res.json()["id"]

    cost_code_res = client.post("/api/v1/cost-codes", json={
        "code": f"03-{uuid4().hex[:4].upper()}",
        "name": "Concrete Works",
        "description": "Concrete & Reinforcement Works"
    }, headers=auth_headers)
    assert cost_code_res.status_code in [200, 201], cost_code_res.text
    cost_code_id = cost_code_res.json()["id"]

    # 2. Create Materials
    mat_code = f"MAT-TEST-{uuid4().hex[:4].upper()}"
    mat_res = client.post("/api/v1/inventory/materials", json={
        "material_code": mat_code,
        "name": "High-Grade Structural Steel",
        "description": "Grade 60 16mm rebar",
        "category": "Metals & Rebar",
        "base_unit": "TON"
    }, headers=auth_headers)
    assert mat_res.status_code == 201, mat_res.text
    material_id = mat_res.json()["id"]

    mats_list = client.get("/api/v1/inventory/materials", headers=auth_headers)
    assert mats_list.status_code == 200
    assert any(m["id"] == material_id for m in mats_list.json())

    # 3. Create Warehouses
    wh1_res = client.post("/api/v1/inventory/warehouses", json={
        "code": f"WH-C-{uuid4().hex[:4].upper()}",
        "name": "Central Testing Depot",
        "location": "Central Yard A",
        "type": "CENTRAL"
    }, headers=auth_headers)
    assert wh1_res.status_code == 201, wh1_res.text
    wh1_id = wh1_res.json()["id"]

    wh2_res = client.post("/api/v1/inventory/warehouses", json={
        "code": f"WH-S-{uuid4().hex[:4].upper()}",
        "name": "Site Staging Yard",
        "location": "Project Staging Bay 3",
        "type": "PROJECT",
        "project_id": project_id
    }, headers=auth_headers)
    assert wh2_res.status_code == 201, wh2_res.text
    wh2_id = wh2_res.json()["id"]

    wh_list = client.get("/api/v1/inventory/warehouses", headers=auth_headers)
    assert wh_list.status_code == 200
    assert any(w["id"] == wh1_id for w in wh_list.json())

    # 4. Create Supplier and Purchase Order
    sup_res = client.post("/api/v1/suppliers/", json={
        "name": f"Apex Metal Works {uuid4().hex[:4]}",
        "legal_name": "Apex Metal Works LLC",
        "tax_identifier": f"TRN-{uuid4().hex[:8].upper()}",
        "status": "ACTIVE"
    }, headers=auth_headers)
    assert sup_res.status_code == 201, sup_res.text
    supplier_id = sup_res.json()["id"]

    po_res = client.post("/api/v1/purchase-orders/", json={
        "po_number": f"PO-INV-{uuid4().hex[:6].upper()}",
        "supplier_id": supplier_id,
        "project_id": project_id,
        "order_date": "2026-09-07",
        "currency": "USD",
        "lines": [
            {
                "material_id": material_id,
                "cost_code_id": cost_code_id,
                "item_description": "High-Grade Structural Steel",
                "unit": "TON",
                "quantity": 100,
                "unit_price": 750.00,
                "amount": 75000.00
            }
        ]
    }, headers=auth_headers)
    assert po_res.status_code == 201, po_res.text
    po_data = po_res.json()
    po_id = po_data["id"]
    po_line_id = po_data["lines"][0]["id"]

    # 5. Goods Receipt Note (GRN)
    grn_res = client.post("/api/v1/inventory/goods-receipts", json={
        "receipt_number": f"GRN-TEST-{uuid4().hex[:6].upper()}",
        "purchase_order_id": po_id,
        "supplier_id": supplier_id,
        "warehouse_id": wh1_id,
        "date": "2026-09-07",
        "notes": "Delivered in good condition with test certs",
        "lines": [
            {
                "purchase_order_line_id": po_line_id,
                "material_id": material_id,
                "received_quantity": 50,
                "accepted_quantity": 50,
                "rejected_quantity": 0,
                "unit_cost": 750.00,
                "notes": "Verified against mill certificate"
            }
        ]
    }, headers=auth_headers)
    assert grn_res.status_code in [200, 201], grn_res.text
    grn_data = grn_res.json()
    assert grn_data["status"] == "POSTED"
    grn_id = grn_data["id"]

    # List goods receipts
    grn_list = client.get("/api/v1/inventory/goods-receipts", headers=auth_headers)
    assert grn_list.status_code == 200
    assert any(g["id"] == grn_id for g in grn_list.json())

    # Verify inventory detailed balance
    bal_res = client.get("/api/v1/inventory/balances/detail", headers=auth_headers)
    assert bal_res.status_code == 200
    bals = bal_res.json()
    target_bal = next((b for b in bals if b["material_id"] == material_id and b["warehouse_id"] == wh1_id), None)
    assert target_bal is not None
    assert Decimal(str(target_bal["quantity"])) >= Decimal("50.0")

    # 6. Material Issue to Project Site
    issue_res = client.post("/api/v1/inventory/material-issues", json={
        "issue_number": f"ISS-TEST-{uuid4().hex[:6].upper()}",
        "warehouse_id": wh1_id,
        "project_id": project_id,
        "cost_code_id": cost_code_id,
        "date": "2026-09-07",
        "purpose": "Tower core column cage fabrication",
        "lines": [
            {
                "material_id": material_id,
                "quantity": 15,
                "notes": "For floor 1 columns"
            }
        ]
    }, headers=auth_headers)
    assert issue_res.status_code in [200, 201], issue_res.text
    issue_data = issue_res.json()
    assert issue_data["status"] == "POSTED"
    issue_id = issue_data["id"]

    # List material issues
    issue_list = client.get("/api/v1/inventory/material-issues", headers=auth_headers)
    assert issue_list.status_code == 200
    assert any(i["id"] == issue_id for i in issue_list.json())

    # 7. Stock Transfer between Warehouses
    transfer_res = client.post("/api/v1/inventory/transfers", json={
        "transfer_number": f"TRF-TEST-{uuid4().hex[:6].upper()}",
        "source_warehouse_id": wh1_id,
        "destination_warehouse_id": wh2_id,
        "date": "2026-09-07",
        "notes": "Inter-depot buffer transfer",
        "lines": [
            {
                "material_id": material_id,
                "quantity": 10,
                "notes": "Truck batch 01"
            }
        ]
    }, headers=auth_headers)
    assert transfer_res.status_code in [200, 201], transfer_res.text
    transfer_data = transfer_res.json()
    assert transfer_data["status"] == "POSTED"
    transfer_id = transfer_data["id"]

    # List transfers
    transfer_list = client.get("/api/v1/inventory/transfers", headers=auth_headers)
    assert transfer_list.status_code == 200
    assert any(t["id"] == transfer_id for t in transfer_list.json())

    # 8. Inventory Summary
    sum_res = client.get("/api/v1/inventory/summary", headers=auth_headers)
    assert sum_res.status_code == 200, sum_res.text
    summary = sum_res.json()
    assert summary["total_items_count"] >= 1
    assert summary["total_warehouses_count"] >= 2
    assert summary["total_receipts_count"] >= 1
    assert summary["total_issues_count"] >= 1
    assert summary["total_transfers_count"] >= 1
    assert Decimal(str(summary["total_valuation"])) > 0
