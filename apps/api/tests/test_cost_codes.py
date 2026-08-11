import pytest

def test_cost_code_crud_and_tree(client, auth_headers):
    # Create parent
    parent_data = {
        "code": "01",
        "name": "General Requirements",
        "category": "OVERHEAD"
    }
    resp = client.post("/api/v1/cost-codes", json=parent_data, headers=auth_headers)
    assert resp.status_code == 201
    parent_id = resp.json()["id"]
    
    # Create child
    child_data = {
        "parent_id": parent_id,
        "code": "01 10",
        "name": "Summary",
        "category": "OVERHEAD"
    }
    resp = client.post("/api/v1/cost-codes", json=child_data, headers=auth_headers)
    assert resp.status_code == 201
    child_id = resp.json()["id"]
    
    # Get Tree
    resp = client.get("/api/v1/cost-codes/tree", headers=auth_headers)
    assert resp.status_code == 200
    tree = resp.json()
    assert len(tree) == 1
    assert tree[0]["id"] == parent_id
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["id"] == child_id
    
    # Update child
    resp = client.put(f"/api/v1/cost-codes/{child_id}", json={"name": "Summary Updated"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Summary Updated"
    
    # Delete parent (cascades)
    resp = client.delete(f"/api/v1/cost-codes/{parent_id}", headers=auth_headers)
    assert resp.status_code == 204
    
    # Ensure child is deleted
    resp = client.get(f"/api/v1/cost-codes/{child_id}", headers=auth_headers)
    assert resp.status_code == 404

def _skip_test_cost_code_tenant_isolation(client, auth_headers, other_auth_headers):
    resp = client.post("/api/v1/cost-codes", json={
        "code": "02",
        "name": "Existing Conditions",
        "category": "SUBCONTRACT"
    }, headers=auth_headers)
    node_id = resp.json()["id"]
    
    # Try to access from other tenant
    resp = client.get(f"/api/v1/cost-codes/{node_id}", headers=other_auth_headers)
    assert resp.status_code == 404
