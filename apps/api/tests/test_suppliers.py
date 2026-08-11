import uuid
from app.models.suppliers import SupplierStatus

def test_create_supplier(client, auth_headers):
    payload = {
        "name": "Acme Steel Corp",
        "legal_name": "Acme Steel Corporation LLC",
        "tax_identifier": "TX-123456",
        "address": "123 Industrial Way",
        "status": SupplierStatus.ACTIVE,
        "contacts": [
            {
                "name": "John Doe",
                "email": "john@acme.com",
                "phone": "+1-555-1234",
                "role": "Sales Manager"
            }
        ]
    }
    
    response = client.post("/api/v1/suppliers/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Acme Steel Corp"
    assert data["status"] == "ACTIVE"
    assert len(data["contacts"]) == 1
    assert data["contacts"][0]["name"] == "John Doe"

def test_get_suppliers(client, auth_headers):
    response = client.get("/api/v1/suppliers/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_supplier_tenant_isolation(client, auth_headers):
    # Create supplier in Tenant A
    payload = {
        "name": "Isolated Supplier",
        "status": SupplierStatus.ACTIVE,
        "contacts": []
    }
    res = client.post("/api/v1/suppliers/", json=payload, headers=auth_headers)
    supplier_id = res.json()["id"]

    # Try to fetch from Tenant B
    invalid_headers = auth_headers.copy()
    invalid_headers["X-Tenant-ID"] = str(uuid.uuid4())
    
    res2 = client.get(f"/api/v1/suppliers/{supplier_id}", headers=invalid_headers)
    assert res2.status_code == 404
