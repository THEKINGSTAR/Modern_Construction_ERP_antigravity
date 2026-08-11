import uuid
from app.models.suppliers import SupplierStatus

def test_purchase_order_lifecycle(client, auth_headers):
    # 1. Create Project
    res = client.post("/api/v1/projects/", json={
        "project_number": "PRJ-PO-001", "name": "PO Test Project", "status": "ACTIVE"
    }, headers=auth_headers)
    project_id = res.json()["id"]

    # 2. Create Supplier
    res = client.post("/api/v1/suppliers/", json={
        "name": "Supplier B", "status": SupplierStatus.ACTIVE, "contacts": []
    }, headers=auth_headers)
    supplier_id = res.json()["id"]

    # 3. Create PO
    po_payload = {
        "po_number": "PO-001",
        "project_id": project_id,
        "supplier_id": supplier_id,
        "currency": "USD",
        "lines": [
            {
                "item_description": "Cement",
                "unit": "TON",
                "quantity": "20.0000",
                "unit_price": "50.0000",
                "amount": "1000.0000"
            }
        ]
    }
    response = client.post("/api/v1/purchase-orders/", json=po_payload, headers=auth_headers)
    assert response.status_code == 201
    po_id = response.json()["id"]
    assert response.json()["status"] == "DRAFT"
    assert response.json()["total_amount"] == "1000.0000"

    # 4. Issue PO
    issue_res = client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=auth_headers)
    assert issue_res.status_code == 200

    get_res = client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_headers)
    assert get_res.json()["status"] == "ISSUED"

    # 5. Cancel PO
    cancel_res = client.post(f"/api/v1/purchase-orders/{po_id}/cancel", headers=auth_headers)
    assert cancel_res.status_code == 200

    get_res2 = client.get(f"/api/v1/purchase-orders/{po_id}", headers=auth_headers)
    assert get_res2.json()["status"] == "CANCELLED"

def test_purchase_order_amount_validation(client, auth_headers):
    # Create Supplier
    res = client.post("/api/v1/suppliers/", json={
        "name": "Supplier C", "status": SupplierStatus.ACTIVE, "contacts": []
    }, headers=auth_headers)
    supplier_id = res.json()["id"]

    # Invalid PO (amount != quantity * unit_price)
    po_payload = {
        "po_number": "PO-002",
        "supplier_id": supplier_id,
        "lines": [
            {
                "item_description": "Cement",
                "unit": "TON",
                "quantity": "20.0000",
                "unit_price": "50.0000",
                "amount": "900.0000" # Invalid
            }
        ]
    }
    response = client.post("/api/v1/purchase-orders/", json=po_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "exactly equal quantity * unit_price" in response.json()["detail"]
