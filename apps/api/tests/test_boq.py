import pytest
from httpx import AsyncClient
import uuid
from decimal import Decimal

def test_boq_lifecycle(client, auth_headers):
    # 1. Create a project
    project_payload = {
        "project_number": "BOQ-001",
        "name": "BOQ Project",
        "description": "Project for BOQ testing",
        "status": "PLANNING"
    }
    response = client.post("/api/v1/projects/", json=project_payload, headers=auth_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # 2. Create a BOQ
    boq_payload = {
        "name": "Main BOQ",
        "project_id": project_id
    }
    response = client.post("/api/v1/boqs/", json=boq_payload, headers=auth_headers)
    assert response.status_code == 201
    boq_data = response.json()
    boq_id = boq_data["id"]
    current_rev_id = boq_data["current_revision_id"]
    
    # 3. Add item to BOQ Revision
    item_payload = {
        "item_code": "01-01",
        "description": "Concrete works",
        "unit": "m3",
        "quantity": "10.5000",
        "unit_rate": "150.2500"
    }
    response = client.post(f"/api/v1/boqs/revisions/{current_rev_id}/items", json=item_payload, headers=auth_headers)
    assert response.status_code == 201
    item_data = response.json()
    
    # Assert Decimal Arithmetic (10.5 * 150.25 = 1577.625)
    assert str(item_data["amount"]) == "1577.6250"
    
    # 4. Fetch Revision with Items
    response = client.get(f"/api/v1/boqs/revisions/{current_rev_id}", headers=auth_headers)
    assert response.status_code == 200
    rev_data = response.json()
    assert len(rev_data["items"]) == 1
    
    # 5. Create a new Revision
    response = client.post(f"/api/v1/boqs/{boq_id}/revisions", headers=auth_headers)
    assert response.status_code == 200
    new_rev_data = response.json()
    new_rev_id = new_rev_data["id"]
    assert new_rev_data["version_number"] == 2
    
    # Verify items were copied
    response = client.get(f"/api/v1/boqs/revisions/{new_rev_id}", headers=auth_headers)
    assert response.status_code == 200
    new_rev_items = response.json()["items"]
    assert len(new_rev_items) == 1
    assert new_rev_items[0]["item_code"] == "01-01"


