import pytest
from fastapi.testclient import TestClient

def test_get_projects_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/projects/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_create_project(client: TestClient, auth_headers: dict):
    # First create a client to associate
    client_response = client.post("/api/v1/clients/", json={
        "name": "Project Client",
        "status": "ACTIVE"
    }, headers=auth_headers)
    client_id = client_response.json()["id"]

    project_data = {
        "project_number": "PRJ-2026-001",
        "name": "Downtown Skyscraper",
        "description": "A new 50-story commercial building",
        "client_id": client_id,
        "status": "PLANNING",
        "base_currency": "USD"
    }
    response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["project_number"] == "PRJ-2026-001"
    assert data["name"] == "Downtown Skyscraper"
    assert "id" in data
    
    # Retrieve the project
    project_id = data["id"]
    get_response = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Downtown Skyscraper"

def test_update_project(client: TestClient, auth_headers: dict):
    project_data = {
        "project_number": "PRJ-2026-002",
        "name": "Highway Expansion",
        "status": "BIDDING"
    }
    response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    update_data = {
        "name": "Highway Expansion Phase 1",
        "status": "AWARDED"
    }
    update_response = client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=auth_headers)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Highway Expansion Phase 1"
    assert data["status"] == "AWARDED"

def test_delete_project(client: TestClient, auth_headers: dict):
    project_data = {
        "project_number": "PRJ-DEL-001",
        "name": "To Be Cancelled",
        "status": "CANCELLED"
    }
    response = client.post("/api/v1/projects/", json=project_data, headers=auth_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    
    delete_response = client.delete(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    
    get_response = client.get(f"/api/v1/projects/{project_id}", headers=auth_headers)
    assert get_response.status_code == 404
