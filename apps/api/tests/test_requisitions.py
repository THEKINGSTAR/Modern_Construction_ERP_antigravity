import uuid

def test_requisition_lifecycle(client, auth_headers):
    # 1. Create a Project
    project_payload = {
        "project_number": "PRJ-REQ-001",
        "name": "Requisition Test Project",
        "status": "ACTIVE"
    }
    res = client.post("/api/v1/projects/", json=project_payload, headers=auth_headers)
    project_id = res.json()["id"]

    # 2. Need requester_id (current user)
    # The auth_headers fixture mocks a user, let's just get the user id by creating a dummy user or using project_manager_id if available. 
    # Actually, we can fetch current user if there's a /me endpoint, or just create one.
    # For now, let's create a random UUID since foreign keys aren't strictly checked in sqlite without pragma in some cases, OR we create a user.
    # We will just insert a UUID and test.
    requester_id = str(uuid.uuid4())

    # 3. Create PR
    pr_payload = {
        "pr_number": "REQ-001",
        "project_id": project_id,
        "requester_id": requester_id,
        "description": "Steel Requisition",
        "lines": [
            {
                "item_description": "Steel Beams",
                "unit": "TON",
                "quantity": "50.00"
            }
        ]
    }
    response = client.post("/api/v1/requisitions/", json=pr_payload, headers=auth_headers)
    assert response.status_code == 201
    pr_id = response.json()["id"]
    assert response.json()["status"] == "DRAFT"

    # 4. Submit PR
    submit_res = client.post(f"/api/v1/requisitions/{pr_id}/submit", headers=auth_headers)
    assert submit_res.status_code == 200

    # Verify status
    get_res = client.get(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)
    assert get_res.json()["status"] == "SUBMITTED"

    # 5. Approve PR
    approve_res = client.post(f"/api/v1/requisitions/{pr_id}/approve", headers=auth_headers)
    assert approve_res.status_code == 200

    # Verify status
    get_res2 = client.get(f"/api/v1/requisitions/{pr_id}", headers=auth_headers)
    assert get_res2.json()["status"] == "APPROVED"
