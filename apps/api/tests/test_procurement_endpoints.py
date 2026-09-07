import pytest
from uuid import uuid4
from decimal import Decimal

def test_procurement_lifecycle(client, test_user, db_session, auth_headers):
    # 1. Test Suppliers
    sup_res = client.post("/api/v1/suppliers/", json={
        "name": f"Atlas Structural Rebar Mills {uuid4().hex[:4]}",
        "legal_name": "Atlas Structural Rebar Mills LLC",
        "tax_identifier": f"TRN-{uuid4().hex[:8].upper()}",
        "address": "Industrial City Zone 4",
        "status": "ACTIVE",
        "contacts": [
            {
                "name": "Tariq Mansour",
                "email": "tariq@atlasrebar.com",
                "phone": "+971-4-888-9999",
                "role": "Sales Director"
            }
        ]
    }, headers=auth_headers)
    assert sup_res.status_code == 201, sup_res.text
    supplier_id = sup_res.json()["id"]

    sup_list = client.get("/api/v1/suppliers/", headers=auth_headers)
    assert sup_list.status_code == 200
    assert any(s["id"] == supplier_id for s in sup_list.json())

    # Create a test project for procurement
    prj_res = client.post("/api/v1/projects/", json={
        "project_number": f"PRJ-PROC-{uuid4().hex[:6].upper()}",
        "name": "Procurement Test Tower",
        "status": "ACTIVE"
    }, headers=auth_headers)
    assert prj_res.status_code == 201, prj_res.text
    project_id = prj_res.json()["id"]

    # 2. Test Purchase Requisition
    pr_res = client.post("/api/v1/requisitions/", json={
        "pr_number": f"PR-TEST-{uuid4().hex[:6].upper()}",
        "project_id": project_id,
        "requester_id": str(test_user.id),
        "description": "High tensile steel rebar supply",
        "status": "DRAFT",
        "lines": [
            {
                "item_description": "16mm Deformed Steel Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0
            }
        ]
    }, headers=auth_headers)
    assert pr_res.status_code == 201, pr_res.text
    pr_data = pr_res.json()
    pr_id = pr_data["id"]
    assert pr_data["status"] == "DRAFT"

    # Submit and Approve Requisition
    sub_res = client.post(f"/api/v1/requisitions/{pr_id}/submit", headers=auth_headers)
    assert sub_res.status_code == 200, sub_res.text

    app_res = client.post(f"/api/v1/requisitions/{pr_id}/approve", headers=auth_headers)
    assert app_res.status_code == 200, app_res.text

    # List Requisitions
    pr_list = client.get("/api/v1/requisitions/", headers=auth_headers)
    assert pr_list.status_code == 200
    assert any(p["id"] == pr_id for p in pr_list.json())

    # 3. Test RFQ
    rfq_res = client.post("/api/v1/rfqs/", json={
        "rfq_number": f"RFQ-TEST-{uuid4().hex[:6].upper()}",
        "project_id": project_id,
        "requisition_id": pr_id,
        "title": "Supply of Grade 60 Steel Rebar",
        "description": "50 tons delivery to site",
        "lines": [
            {
                "item_description": "16mm Deformed Steel Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0
            }
        ]
    }, headers=auth_headers)
    assert rfq_res.status_code == 201, rfq_res.text
    rfq_data = rfq_res.json()
    rfq_id = rfq_data["id"]
    rfq_line_id = rfq_data["lines"][0]["id"]

    # Publish RFQ
    pub_res = client.post(f"/api/v1/rfqs/{rfq_id}/publish", headers=auth_headers)
    assert pub_res.status_code == 200, pub_res.text

    # List RFQs
    rfq_list = client.get("/api/v1/rfqs/", headers=auth_headers)
    assert rfq_list.status_code == 200
    assert any(r["id"] == rfq_id for r in rfq_list.json())

    # 4. Test Supplier Quotation
    quote_res = client.post("/api/v1/quotations/", json={
        "rfq_id": rfq_id,
        "supplier_id": supplier_id,
        "quotation_reference": "Q-ATLAS-2026-01",
        "currency": "USD",
        "notes": "Valid for 30 calendar days",
        "lines": [
            {
                "rfq_line_id": rfq_line_id,
                "unit_price": 850.0,
                "quoted_quantity": 50.0,
                "amount": 42500.0,
                "lead_time_days": 10
            }
        ]
    }, headers=auth_headers)
    assert quote_res.status_code == 201, quote_res.text
    quote_id = quote_res.json()["id"]

    # Submit and Accept Quotation
    qsub_res = client.post(f"/api/v1/quotations/{quote_id}/submit", headers=auth_headers)
    assert qsub_res.status_code == 200, qsub_res.text

    qacc_res = client.post(f"/api/v1/quotations/{quote_id}/accept", headers=auth_headers)
    assert qacc_res.status_code == 200, qacc_res.text

    # List Quotations
    quote_list = client.get("/api/v1/quotations/", headers=auth_headers)
    assert quote_list.status_code == 200
    assert any(q["id"] == quote_id for q in quote_list.json())

    # 5. Test Purchase Order
    po_res = client.post("/api/v1/purchase-orders/", json={
        "po_number": f"PO-TEST-{uuid4().hex[:6].upper()}",
        "project_id": project_id,
        "supplier_id": supplier_id,
        "quotation_id": quote_id,
        "currency": "USD",
        "total_amount": 42500.0,
        "notes": "Deliver per site call-off schedule",
        "lines": [
            {
                "item_description": "16mm Deformed Steel Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0,
                "unit_price": 850.0,
                "amount": 42500.0
            }
        ]
    }, headers=auth_headers)
    assert po_res.status_code == 201, po_res.text
    po_data = po_res.json()
    po_id = po_data["id"]
    assert float(po_data["total_amount"]) == 42500.0

    # Issue Purchase Order
    iss_res = client.post(f"/api/v1/purchase-orders/{po_id}/issue", headers=auth_headers)
    assert iss_res.status_code == 200, iss_res.text

    # List Purchase Orders
    po_list = client.get("/api/v1/purchase-orders/", headers=auth_headers)
    assert po_list.status_code == 200
    assert any(p["id"] == po_id for p in po_list.json())

    # Test Procurement Summary
    summary_res = client.get("/api/v1/purchase-orders/summary", headers=auth_headers)
    assert summary_res.status_code == 200, summary_res.text
    summary_data = summary_res.json()
    assert float(summary_data["total_po_value"]) >= 42500.0
    assert summary_data["active_pos_count"] >= 1
    assert summary_data["approved_suppliers_count"] >= 1
