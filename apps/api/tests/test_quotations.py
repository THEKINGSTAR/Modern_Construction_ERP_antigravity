import uuid
from app.models.suppliers import SupplierStatus

def test_quotation_lifecycle(client, auth_headers):
    # 1. Create Project
    res = client.post("/api/v1/projects/", json={
        "project_number": "PRJ-QT-001", "name": "Quote Test", "status": "ACTIVE"
    }, headers=auth_headers)
    project_id = res.json()["id"]

    # 2. Create Supplier
    res = client.post("/api/v1/suppliers/", json={
        "name": "Supplier A", "status": SupplierStatus.ACTIVE, "contacts": []
    }, headers=auth_headers)
    supplier_id = res.json()["id"]

    # 3. Create & Publish RFQ
    rfq_res = client.post("/api/v1/rfqs/", json={
        "rfq_number": "RFQ-Q-001", "project_id": project_id, "title": "Test RFQ",
        "lines": [{"item_description": "Steel", "unit": "TON", "quantity": "10"}]
    }, headers=auth_headers)
    rfq_id = rfq_res.json()["id"]
    rfq_line_id = rfq_res.json()["lines"][0]["id"]
    
    client.post(f"/api/v1/rfqs/{rfq_id}/publish", headers=auth_headers)

    # 4. Create Quotation
    quote_payload = {
        "rfq_id": rfq_id,
        "supplier_id": supplier_id,
        "lines": [
            {
                "rfq_line_id": rfq_line_id,
                "unit_price": "100.00",
                "quoted_quantity": "10.00",
                "amount": "1000.00"
            }
        ]
    }
    response = client.post("/api/v1/quotations/", json=quote_payload, headers=auth_headers)
    assert response.status_code == 201
    quote_id = response.json()["id"]
    assert response.json()["status"] == "DRAFT"

    # 5. Submit Quotation
    submit_res = client.post(f"/api/v1/quotations/{quote_id}/submit", headers=auth_headers)
    assert submit_res.status_code == 200

    # 6. Accept Quotation
    accept_res = client.post(f"/api/v1/quotations/{quote_id}/accept", headers=auth_headers)
    assert accept_res.status_code == 200

    get_res = client.get(f"/api/v1/quotations/{quote_id}", headers=auth_headers)
    assert get_res.json()["status"] == "ACCEPTED"
