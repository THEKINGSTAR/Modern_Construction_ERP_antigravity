import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_approval_workflow_engine(client: TestClient, db_session: Session, auth_headers, test_tenant):
    entity_id = str(uuid4())
    
    # 1. Create Rules
    # Step 1: Project Manager
    r1 = client.post("/api/v1/approvals/rules", json={
        "entity_type": "PURCHASE_ORDER",
        "min_amount": "0",
        "max_amount": "10000",
        "required_role": "PROJECT_MANAGER",
        "step_order": 1
    }, headers=auth_headers)
    assert r1.status_code == 201

    # Step 2: Regional Manager
    r2 = client.post("/api/v1/approvals/rules", json={
        "entity_type": "PURCHASE_ORDER",
        "min_amount": "5000",
        "max_amount": "50000",
        "required_role": "REGIONAL_MANAGER",
        "step_order": 2
    }, headers=auth_headers)
    assert r2.status_code == 201

    # 2. Trigger Workflow (Amount = 6000, should trigger both rules)
    wf_res = client.post(f"/api/v1/approvals/workflows?entity_type=PURCHASE_ORDER&entity_id={entity_id}&amount=6000", headers=auth_headers)
    assert wf_res.status_code == 201
    workflow = wf_res.json()
    wf_id = workflow["id"]
    
    assert workflow["status"] == "IN_PROGRESS"
    assert workflow["current_step_order"] == 1
    assert len(workflow["steps"]) == 2

    # 3. Process Step 1 (Approve)
    a1_res = client.post(f"/api/v1/approvals/workflows/{wf_id}/action", json={
        "action": "APPROVE",
        "comments": "Looks good to me"
    }, headers=auth_headers)
    assert a1_res.status_code == 200
    wf_state = a1_res.json()
    assert wf_state["current_step_order"] == 2
    assert wf_state["status"] == "IN_PROGRESS"

    # 4. Process Step 2 (Approve) -> Should finish workflow
    a2_res = client.post(f"/api/v1/approvals/workflows/{wf_id}/action", json={
        "action": "APPROVE",
        "comments": "Approved by Regional Manager"
    }, headers=auth_headers)
    assert a2_res.status_code == 200
    final_wf = a2_res.json()
    
    assert final_wf["status"] == "APPROVED"
