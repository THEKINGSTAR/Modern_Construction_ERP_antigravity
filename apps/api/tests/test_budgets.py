import pytest
from httpx import AsyncClient
import uuid
from decimal import Decimal

def test_budget_calculations(client, auth_headers):
    # 1. Create a project
    project_payload = {
        "project_number": "BUD-001",
        "name": "Budget Project",
        "description": "Project for Budget testing",
        "status": "PLANNING"
    }
    response = client.post("/api/v1/projects/", json=project_payload, headers=auth_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    # 2. Create a cost code
    cc_payload = {
        "code": "01",
        "name": "General Requirements",
        "category": "OTHER_DIRECT"
    }
    response = client.post("/api/v1/cost-codes/", json=cc_payload, headers=auth_headers)
    assert response.status_code == 201
    cc_id = response.json()["id"]
    
    # 3. Create a Budget
    budget_payload = {
        "name": "Main Budget",
        "project_id": project_id
    }
    response = client.post("/api/v1/budgets/", json=budget_payload, headers=auth_headers)
    assert response.status_code == 201
    budget_id = response.json()["id"]
    
    # 4. Add a budget line
    line_payload = {
        "cost_code_id": cc_id,
        "original_budget": "100000.0000",
        "approved_changes": "5000.0000"
    }
    response = client.post(f"/api/v1/budgets/{budget_id}/lines", json=line_payload, headers=auth_headers)
    assert response.status_code == 201
    line_data = response.json()
    
    # Assert calculated fields
    # current_budget = 100000 + 5000 = 105000
    assert str(line_data["current_budget"]) == "105000.0000"
    # variance = current - (committed + actual) -> 105000 - 0 = 105000
    assert str(line_data["variance"]) == "105000.0000"
    
    # 5. Fetch Summary
    response = client.get(f"/api/v1/budgets/{budget_id}/summary", headers=auth_headers)
    assert response.status_code == 200
    summary_data = response.json()
    assert len(summary_data["lines"]) == 1
    assert str(summary_data["lines"][0]["current_budget"]) == "105000.0000"


