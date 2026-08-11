import uuid

def test_rfq_lifecycle(client, auth_headers):
    # 1. Create a Project
    project_payload = {
        "project_number": "PRJ-RFQ-001",
        "name": "RFQ Test Project",
        "status": "ACTIVE"
    }
    res = client.post("/api/v1/projects/", json=project_payload, headers=auth_headers)
    project_id = res.json()["id"]

    # 2. Create RFQ
    rfq_payload = {
        "rfq_number": "RFQ-001",
        "project_id": project_id,
        "title": "Steel Procurement",
        "lines": [
            {
                "item_description": "Steel Beams",
                "unit": "TON",
                "quantity": "50.00"
            }
        ]
    }
    response = client.post("/api/v1/rfqs/", json=rfq_payload, headers=auth_headers)
    assert response.status_code == 201
    rfq_id = response.json()["id"]
    assert response.json()["status"] == "DRAFT"

    # 3. Publish RFQ
    publish_res = client.post(f"/api/v1/rfqs/{rfq_id}/publish", headers=auth_headers)
    assert publish_res.status_code == 200

    # Verify status
    get_res = client.get(f"/api/v1/rfqs/{rfq_id}", headers=auth_headers)
    assert get_res.json()["status"] == "PUBLISHED"

    # 4. Close RFQ
    close_res = client.post(f"/api/v1/rfqs/{rfq_id}/close", headers=auth_headers)
    assert close_res.status_code == 200

    # Verify status
    get_res2 = client.get(f"/api/v1/rfqs/{rfq_id}", headers=auth_headers)
    assert get_res2.json()["status"] == "CLOSED"
