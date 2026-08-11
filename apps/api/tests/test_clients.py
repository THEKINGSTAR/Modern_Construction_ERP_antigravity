import pytest
from fastapi.testclient import TestClient

def test_get_clients_empty(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/clients/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_create_client(client: TestClient, auth_headers: dict):
    client_data = {
        "name": "Acme Corp",
        "legal_name": "Acme Corporation Inc.",
        "status": "ACTIVE",
        "contacts": [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@acme.com",
                "role": "CEO",
                "is_primary": True
            }
        ]
    }
    response = client.post("/api/v1/clients/", json=client_data, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Corp"
    assert "id" in data
    assert len(data["contacts"]) == 1
    assert data["contacts"][0]["first_name"] == "John"
    
    # Retrieve the client
    client_id = data["id"]
    get_response = client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Acme Corp"
    
def test_update_client(client: TestClient, auth_headers: dict):
    client_data = {
        "name": "Global Builders",
        "status": "ACTIVE"
    }
    response = client.post("/api/v1/clients/", json=client_data, headers=auth_headers)
    assert response.status_code == 201
    client_id = response.json()["id"]
    
    update_data = {
        "name": "Global Builders Inc.",
        "status": "INACTIVE"
    }
    update_response = client.put(f"/api/v1/clients/{client_id}", json=update_data, headers=auth_headers)
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Global Builders Inc."
    assert data["status"] == "INACTIVE"

def test_delete_client(client: TestClient, auth_headers: dict):
    client_data = {
        "name": "To Be Deleted",
        "status": "ACTIVE"
    }
    response = client.post("/api/v1/clients/", json=client_data, headers=auth_headers)
    assert response.status_code == 201
    client_id = response.json()["id"]
    
    delete_response = client.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    
    get_response = client.get(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert get_response.status_code == 404
