import pytest
from httpx import AsyncClient
import uuid
from decimal import Decimal

def test_estimate_lifecycle(client, auth_headers):
    # 1. Create a project
    project_payload = {
        "project_number": "EST-001",
        "name": "Estimate Project",
        "description": "Project for Estimate testing",
        "status": "PLANNING"
    }
    response = client.post("/api/v1/projects/", json=project_payload, headers=auth_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # 2. Create an Estimate
    estimate_payload = {
        "name": "Main Estimate",
        "project_id": project_id
    }
    response = client.post("/api/v1/estimates/", json=estimate_payload, headers=auth_headers)
    assert response.status_code == 201
    est_data = response.json()
    est_id = est_data["id"]
    current_rev_id = est_data["current_revision_id"]
    
    # 3. Add item to Estimate Revision
    item_payload = {
        "item_code": "01-02",
        "description": "Steel works",
        "unit": "ton",
        "quantity": "50.0000",
        "unit_rate": "1200.0000"
    }
    response = client.post(f"/api/v1/estimates/revisions/{current_rev_id}/items", json=item_payload, headers=auth_headers)
    assert response.status_code == 201
    item_data = response.json()
    
    # Assert Decimal Arithmetic (50 * 1200 = 60000)
    assert str(item_data["amount"]) == "60000.0000"
    
    # 4. Fetch Revision with Items
    response = client.get(f"/api/v1/estimates/revisions/{current_rev_id}", headers=auth_headers)
    assert response.status_code == 200
    rev_data = response.json()
    assert len(rev_data["items"]) == 1
    
    # 5. Create a new Revision
    response = client.post(f"/api/v1/estimates/{est_id}/revisions", headers=auth_headers)
    assert response.status_code == 200
    new_rev_data = response.json()
    new_rev_id = new_rev_data["id"]
    assert new_rev_data["version_number"] == 2
    
    # Verify items were copied
    response = client.get(f"/api/v1/estimates/revisions/{new_rev_id}", headers=auth_headers)
    assert response.status_code == 200
    new_rev_items = response.json()["items"]
    assert len(new_rev_items) == 1
    assert new_rev_items[0]["item_code"] == "01-02"


