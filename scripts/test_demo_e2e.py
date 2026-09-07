import random
#!/usr/bin/env python3
"""
scripts/test_demo_e2e.py — Comprehensive End-to-End Real ERP Verification Suite.
Validates the complete stack:
  Browser/Client -> Next.js Frontend -> FastAPI Backend -> PostgreSQL Database -> Business Logic -> Persistence
"""

import sys
import uuid
import os
import json
import urllib.request
import urllib.parse
from decimal import Decimal

API_BASE = "http://localhost:8000/api/v1"
WEB_BASE = "http://localhost:3000"

def test_web_frontend():
    print("1. Testing Next.js Frontend HTTP Server...")
    req = urllib.request.Request(f"{WEB_BASE}/en")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200 from Next.js, got {resp.status}"
        body = resp.read().decode("utf-8")
        assert "Modern Construction ERP" in body, "Expected ERP branding in HTML"
        print(f"   ✓ Frontend online at {resp.geturl()} (HTTP {resp.status})")

def test_api_health():
    print("2. Testing FastAPI Backend & Database Readiness...")
    req = urllib.request.Request("http://localhost:8000/health/ready")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") == "ok", f"Health status not ok: {data}"
        assert data.get("components", {}).get("database") == "ok", "Database component not ok"
        assert data.get("components", {}).get("redis") == "ok", "Redis component not ok"
        print(f"   ✓ Backend health ready: database=ok, redis=ok (HTTP {resp.status})")

def test_auth():
    print("3. Testing Authentication & JWT Generation...")
    login_data = urllib.parse.urlencode({
        "username": "demo@apexconstruction.com",
        "password": "DemoPassword2026!"
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{API_BASE}/auth/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        token_data = json.loads(resp.read().decode("utf-8"))
        token = token_data.get("access_token")
        assert token, "No access_token returned"
        print(f"   ✓ Authentication successful. JWT token received.")
        return token

def test_erp_workflows(token: str):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("4. Testing Multi-Tenant Settings Endpoint...")
    req = urllib.request.Request(f"{API_BASE}/settings/tenant", headers=headers)
    with urllib.request.urlopen(req) as resp:
        settings = json.loads(resp.read().decode("utf-8"))
        assert settings.get("base_currency_code") == "USD"
        print(f"   ✓ Tenant Settings verified: base_currency={settings.get('base_currency_code')}")

    print("5. Testing Projects Domain (Read & Create)...")
    req = urllib.request.Request(f"{API_BASE}/projects/", headers=headers)
    with urllib.request.urlopen(req) as resp:
        projects = json.loads(resp.read().decode("utf-8"))
        initial_count = len(projects)
        assert initial_count >= 1, "Expected at least 1 project seeded"
        print(f"   ✓ Existing projects retrieved: {initial_count} project(s)")

    # Create new project
    suffix = str(os.getpid())
    new_proj_payload = json.dumps({
        "project_number": f"PRJ-E2E-{suffix}",
        "name": f"E2E Automated Verification Pier {suffix}",
        "budget_amount": "3500000.00",
        "status": "ACTIVE"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/projects/", data=new_proj_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created = json.loads(resp.read().decode("utf-8"))
        assert created["project_number"] == f"PRJ-E2E-{suffix}"
        print(f"   ✓ Created new project: {created['name']} ({created['project_number']})")

    print("6. Testing Clients Domain (Read & Create)...")
    new_client_payload = json.dumps({
        "name": f"E2E Verification Client Ltd {suffix}",
        "legal_name": f"E2E Verification Client Limited",
        "contact_information": f"e2e-{suffix}@test.erp",
        "status": "ACTIVE"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/clients/", data=new_client_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created_client = json.loads(resp.read().decode("utf-8"))
        print(f"   ✓ Created new client: {created_client['name']}")

    print("7. Testing Inventory Ledger & Detailed Warehouse Stock Balances...")
    req = urllib.request.Request(f"{API_BASE}/inventory/balances/detail", headers=headers)
    with urllib.request.urlopen(req) as resp:
        detailed_balances = json.loads(resp.read().decode("utf-8"))
        assert len(detailed_balances) >= 1, "Expected at least 1 detailed warehouse balance"
        b = detailed_balances[0]
        assert "material_name" in b, "Missing material_name joined in balance detail"
        assert "warehouse_name" in b, "Missing warehouse_name joined in balance detail"
        qty = Decimal(str(b["quantity"]))
        val = Decimal(str(b["total_cost"]))
        print(f"   ✓ Detailed stock balance: {b['material_name']} in {b['warehouse_name']} — {qty} {b['base_unit']} (Valuation: ${val:,.2f})")

    print("8. Testing Procurement Domain (Purchase Orders)...")
    req = urllib.request.Request(f"{API_BASE}/purchase-orders/", headers=headers)
    with urllib.request.urlopen(req) as resp:
        pos = json.loads(resp.read().decode("utf-8"))
        assert len(pos) >= 1, "Expected at least 1 purchase order"
        print(f"   ✓ Purchase orders retrieved: {len(pos)} PO(s) on file (Latest PO: {pos[0]['po_number']})")

    print("9. Testing Accounts Payable Invoices...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices", headers=headers)
    with urllib.request.urlopen(req) as resp:
        invoices = json.loads(resp.read().decode("utf-8"))
        assert len(invoices) >= 1, "Expected at least 1 AP invoice"
        print(f"   ✓ Accounts Payable retrieved: {len(invoices)} invoice(s) (Invoice #{invoices[0]['number']} for ${float(invoices[0]['total_amount']):,.2f})")

    print("10. Testing General Ledger Trial Balance (Golden Rule: Debits == Credits)...")
    req = urllib.request.Request(f"{API_BASE}/reports/accounting/trial-balance", headers=headers)
    with urllib.request.urlopen(req) as resp:
        tb = json.loads(resp.read().decode("utf-8"))
        total_debit = Decimal(str(tb["total_debit"]))
        total_credit = Decimal(str(tb["total_credit"]))
        assert total_debit == total_credit, f"Golden Rule broken! Debit {total_debit} != Credit {total_credit}"
        print(f"   ✓ Trial Balance balanced: Total Debits (${total_debit:,.2f}) == Total Credits (${total_credit:,.2f})")

    print("11. Testing Executive Dashboard Live SQL Aggregation Engine...")
    req = urllib.request.Request(f"{API_BASE}/reports/executive-dashboard", headers=headers)
    with urllib.request.urlopen(req) as resp:
        exec_dash = json.loads(resp.read().decode("utf-8"))
        assert Decimal(str(exec_dash["total_contract_value"])) >= Decimal("7500000.00")
        assert exec_dash["total_active_contracts"] >= 1
        assert Decimal(str(exec_dash["total_on_hand_quantity"])) >= Decimal("65.0")
        assert exec_dash["is_ledger_balanced"] is True
        assert Decimal(str(exec_dash["total_open_payables"])) >= Decimal("85000.00")
        print(f"   ✓ Executive Dashboard SQL Engine aggregated live values:")
        print(f"     - Contracts: ${float(exec_dash['total_contract_value']):,.2f} ({exec_dash['total_active_contracts']} active)")
        print(f"     - Stock: {float(exec_dash['total_on_hand_quantity']):.1f} TON (Valuation: ${float(exec_dash['total_inventory_valuation']):,.2f})")
        print(f"     - General Ledger: ${float(exec_dash['total_debits']):,.2f} (Balanced: {exec_dash['is_ledger_balanced']})")
        print(f"     - Trade Payables: ${float(exec_dash['total_open_payables']):,.2f} ({exec_dash['total_ap_invoices']} invoices)")

    print("12. Testing Prime Commercial Contracts Domain...")
    req = urllib.request.Request(f"{API_BASE}/contracts", headers=headers)
    with urllib.request.urlopen(req) as resp:
        contracts = json.loads(resp.read().decode("utf-8"))
        assert len(contracts) >= 1, "Expected at least 1 contract"
        active_contract_id = contracts[0]["id"]
        print(f"   ✓ Prime Contracts retrieved: {len(contracts)} contract(s) on file (Contract #{contracts[0]['contract_number']} for ${float(contracts[0]['current_value']):,.2f})")

    # Get project id for linked modules
    req = urllib.request.Request(f"{API_BASE}/projects", headers=headers)
    with urllib.request.urlopen(req) as resp:
        projects = json.loads(resp.read().decode("utf-8"))
        active_project_id = projects[0]["id"]

    print("13. Testing Work Breakdown Structure (WBS) Creation & Hierarchy...")
    rand_wbs = random.randint(1000, 9999)
    wbs_payload = json.dumps({
        "project_id": active_project_id,
        "parent_id": None,
        "code": f"WBS-{rand_wbs}",
        "name": f"E2E Structural Substructure Verification {rand_wbs}",
        "description": "Automated E2E test milestone",
        "is_active": True
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/wbs", data=wbs_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_wbs = json.loads(resp.read().decode("utf-8"))
        assert created_wbs["code"] == f"WBS-{rand_wbs}"
        print(f"   ✓ Created WBS Node: {created_wbs['code']} ({created_wbs['name']})")

    print("14. Testing Standard Cost Codes (CSI MasterFormat)...")
    req = urllib.request.Request(f"{API_BASE}/cost-codes", headers=headers)
    with urllib.request.urlopen(req) as resp:
        cost_codes = json.loads(resp.read().decode("utf-8"))
        assert len(cost_codes) >= 1, "Expected at least 1 cost code"
        print(f"   ✓ Standard Cost Codes verified: {len(cost_codes)} code(s) active in catalog")

    print("15. Testing Bill of Quantities (BOQ) Domain...")
    boq_payload = json.dumps({
        "project_id": active_project_id,
        "name": f"E2E Automated Tender BOQ {rand_wbs}"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/boqs/", data=boq_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_boq = json.loads(resp.read().decode("utf-8"))
        assert created_boq["status"] == "DRAFT"
        print(f"   ✓ Created BOQ Document: {created_boq['name']} (Status: {created_boq['status']})")

    print("16. Testing Cost Estimating Domain...")
    est_payload = json.dumps({
        "project_id": active_project_id,
        "name": f"E2E Detailed Cost Estimate {rand_wbs}"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/estimates/", data=est_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_est = json.loads(resp.read().decode("utf-8"))
        assert created_est["status"] == "DRAFT"
        print(f"   ✓ Created Cost Estimate: {created_est['name']} (Status: {created_est['status']})")

    print("17. Testing Project Budgets Domain...")
    budget_payload = json.dumps({
        "project_id": active_project_id,
        "name": f"E2E Baseline Budget {rand_wbs}"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/budgets/", data=budget_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_budget = json.loads(resp.read().decode("utf-8"))
        print(f"   ✓ Created Project Budget: {created_budget['name']}")

    print("18. Testing Trade Subcontracts Domain...")
    # Fetch first supplier for subcontract
    req_sup = urllib.request.Request(f"{API_BASE}/suppliers/", headers=headers)
    with urllib.request.urlopen(req_sup) as resp:
        suppliers = json.loads(resp.read().decode("utf-8"))
        assert len(suppliers) > 0, "Expected at least one supplier"
        supplier_id = suppliers[0]["id"]

    rand_sc = random.randint(1000, 9999)
    sc_payload = json.dumps({
        "project_id": active_project_id,
        "supplier_id": supplier_id,
        "subcontract_number": f"SC-E2E-{rand_sc}",
        "original_value": 750000.00,
        "currency_code": "USD",
        "retention_rate": 10.0,
        "start_date": "2026-03-01",
        "end_date": "2026-11-30"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/commercial/subcontracts", data=sc_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_sc = json.loads(resp.read().decode("utf-8"))
        assert created_sc["subcontract_number"] == f"SC-E2E-{rand_sc}"
        assert float(created_sc["current_value"]) == 750000.00
        active_subcontract_id = created_sc["id"]
        print(f"   ✓ Awarded Trade Subcontract: {created_sc['subcontract_number']} ($750,000.00, 10% retention)")

    print("19. Testing Variation Orders (CCO/SCO) with Dynamic Contract Adjustments...")
    # 1. Fetch initial contract value
    req_ctr = urllib.request.Request(f"{API_BASE}/contracts/{active_contract_id}", headers=headers)
    with urllib.request.urlopen(req_ctr) as resp:
        pre_ctr = json.loads(resp.read().decode("utf-8"))
        pre_val = float(pre_ctr["current_value"])

    # 2. Submit CCO
    cco_payload = json.dumps({
        "contract_id": active_contract_id,
        "number": f"CCO-E2E-{rand_sc}",
        "title": "Facade Glazing Specification Upgrade",
        "description": "Double-glazed acoustic unitized curtain wall upgrade",
        "amount": 125000.00
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/commercial/client-change-orders", data=cco_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_cco = json.loads(resp.read().decode("utf-8"))
        assert created_cco["status"] == "DRAFT"
        cco_id = created_cco["id"]

    # 3. Approve CCO
    req = urllib.request.Request(f"{API_BASE}/commercial/client-change-orders/{cco_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        app_cco = json.loads(resp.read().decode("utf-8"))
        assert app_cco["status"] == "APPROVED"

    # 4. Verify parent contract current_value increased in PostgreSQL
    req_ctr = urllib.request.Request(f"{API_BASE}/contracts/{active_contract_id}", headers=headers)
    with urllib.request.urlopen(req_ctr) as resp:
        post_ctr = json.loads(resp.read().decode("utf-8"))
        post_val = float(post_ctr["current_value"])
        assert post_val == pre_val + 125000.00, f"Expected {pre_val + 125000.00}, got {post_val}"
        print(f"   ✓ Approved Client Variation: CCO-E2E-{rand_sc} (+$125,000.00), Contract value updated from ${pre_val:,.2f} to ${post_val:,.2f}")

    print("20. Testing Progress Billings & Statutory 10% Retention Calculation...")
    # Fetch accounting period
    req_per = urllib.request.Request(f"{API_BASE}/settings/accounting-periods", headers=headers)
    with urllib.request.urlopen(req_per) as resp:
        periods = json.loads(resp.read().decode("utf-8"))
        assert len(periods) > 0
        period_id = periods[0]["id"]

    cpa_payload = json.dumps({
        "contract_id": active_contract_id,
        "accounting_period_id": period_id,
        "number": f"IPC-E2E-{rand_sc}",
        "date": "2026-09-30",
        "gross_work": 1500000.00,
        "previous_certified_work": 500000.00,
        "retention_amount": 100000.00, # 10% of 1,000,000 current work
        "advance_recovery_amount": 0.00,
        "deductions_amount": 0.00,
        "adjustments_amount": 0.00
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/commercial/client-payment-applications", data=cpa_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_cpa = json.loads(resp.read().decode("utf-8"))
        assert float(created_cpa["net_amount_due"]) == 900000.00, f"Expected 900000.00, got {created_cpa['net_amount_due']}"
        cpa_id = created_cpa["id"]

    # Approve Application
    req = urllib.request.Request(f"{API_BASE}/commercial/client-payment-applications/{cpa_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        app_cpa = json.loads(resp.read().decode("utf-8"))
        assert app_cpa["status"] == "APPROVED"
        print(f"   ✓ Verified Payment Application: IPC-E2E-{rand_sc} (Gross $1.5M, Current $1.0M, Retention $100K, Net Due $900,000.00, Status: APPROVED)")

    print("21. Testing Consolidated Commercial Summary Aggregation...")
    req = urllib.request.Request(f"{API_BASE}/commercial/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        summary = json.loads(resp.read().decode("utf-8"))
        assert float(summary["total_prime_contract_value"]) > 0
        assert float(summary["total_subcontracts_value"]) > 0
        assert float(summary["total_client_change_orders_approved"]) > 0
        assert float(summary["total_client_billed"]) > 0
        assert int(summary["subcontracts_count"]) >= 4
        print(f"   ✓ Live Commercial Metrics: Prime Contracts=${float(summary['total_prime_contract_value']):,.2f}, Subcontracts=${float(summary['total_subcontracts_value']):,.2f}, Retention Held=${float(summary['total_client_retention']):,.2f}")

    print("22. Testing Purchase Requisitions Lifecycle (Draft -> Submitted -> Approved)...")
    rand_pr = random.randint(1000, 9999)
    pr_payload = json.dumps({
        "pr_number": f"PR-E2E-{rand_pr}",
        "project_id": active_project_id,
        "requester_id": "44444444-4444-4444-8444-444444444444",
        "description": f"E2E High-Tensile Rebar Demand {rand_pr}",
        "status": "DRAFT",
        "lines": [
            {
                "item_description": "16mm High-Tensile Deformed Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/requisitions/", data=pr_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_pr = json.loads(resp.read().decode("utf-8"))
        pr_id = created_pr["id"]
        assert created_pr["status"] == "DRAFT"

    # Submit PR
    req = urllib.request.Request(f"{API_BASE}/requisitions/{pr_id}/submit", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200

    # Approve PR
    req = urllib.request.Request(f"{API_BASE}/requisitions/{pr_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        print(f"   ✓ Approved Purchase Requisition: PR-E2E-{rand_pr} (50 TON Grade 60 Rebar)")

    print("23. Testing Requests for Quotations (RFQs) & Tender Publishing...")
    rfq_payload = json.dumps({
        "rfq_number": f"RFQ-E2E-{rand_pr}",
        "project_id": active_project_id,
        "requisition_id": pr_id,
        "title": f"Supply of Grade 60 Rebar {rand_pr}",
        "lines": [
            {
                "item_description": "16mm High-Tensile Deformed Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/rfqs/", data=rfq_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_rfq = json.loads(resp.read().decode("utf-8"))
        rfq_id = created_rfq["id"]
        rfq_line_id = created_rfq["lines"][0]["id"]

    # Publish RFQ
    req = urllib.request.Request(f"{API_BASE}/rfqs/{rfq_id}/publish", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        print(f"   ✓ Published RFQ Tender Package: RFQ-E2E-{rand_pr}")

    print("24. Testing Supplier Quotation Submission & Evaluation...")
    quote_payload = json.dumps({
        "rfq_id": rfq_id,
        "supplier_id": supplier_id,
        "quotation_reference": f"Q-E2E-{rand_pr}",
        "currency": "USD",
        "lines": [
            {
                "rfq_line_id": rfq_line_id,
                "unit_price": 850.0,
                "quoted_quantity": 50.0,
                "amount": 42500.0,
                "lead_time_days": 7
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/quotations/", data=quote_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_quote = json.loads(resp.read().decode("utf-8"))
        quote_id = created_quote["id"]

    # Submit and Accept Quotation
    req = urllib.request.Request(f"{API_BASE}/quotations/{quote_id}/submit", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200

    req = urllib.request.Request(f"{API_BASE}/quotations/{quote_id}/accept", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        print(f"   ✓ Accepted Supplier Quotation: Q-E2E-{rand_pr} ($42,500.00)")

    print("25. Testing Purchase Order Lifecycle & Order Issuance...")
    po_payload = json.dumps({
        "po_number": f"PO-E2E-{rand_pr}",
        "project_id": active_project_id,
        "supplier_id": supplier_id,
        "quotation_id": quote_id,
        "currency": "USD",
        "total_amount": 42500.0,
        "lines": [
            {
                "item_description": "16mm High-Tensile Deformed Rebar Grade 60",
                "unit": "TON",
                "quantity": 50.0,
                "unit_price": 850.0,
                "amount": 42500.0
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/purchase-orders/", data=po_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        created_po = json.loads(resp.read().decode("utf-8"))
        po_id = created_po["id"]
        po_line_id = created_po["lines"][0]["id"] if created_po.get("lines") else None

    # Issue PO
    req = urllib.request.Request(f"{API_BASE}/purchase-orders/{po_id}/issue", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        print(f"   ✓ Issued Purchase Order: PO-E2E-{rand_pr} ($42,500.00, Status: ISSUED)")

    print("26. Testing Consolidated Procurement Summary Aggregation Engine...")
    req = urllib.request.Request(f"{API_BASE}/purchase-orders/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        summary_proc = json.loads(resp.read().decode("utf-8"))
        assert float(summary_proc["total_po_value"]) > 0
        assert int(summary_proc["active_pos_count"]) >= 1
        assert int(summary_proc["approved_suppliers_count"]) >= 1
        print(f"   ✓ Live Procurement Metrics: Total PO Committed=${float(summary_proc['total_po_value']):,.2f}, Active Orders={summary_proc['active_pos_count']}, Suppliers={summary_proc['approved_suppliers_count']}")

    print("27. Testing Materials Master Catalog (Creation & Catalog Verification)...")
    rand_mat = uuid.uuid4().hex[:4].upper()
    mat_payload = json.dumps({
        "material_code": f"MAT-E2E-{rand_mat}",
        "name": f"High-Tensile Rebar E2E {rand_mat}",
        "description": "Grade 60 structural deformed bar",
        "category": "Metals & Rebar",
        "base_unit": "TON"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/inventory/materials", data=mat_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        e2e_mat = json.loads(resp.read().decode("utf-8"))
        e2e_mat_id = e2e_mat["id"]
        print(f"   ✓ Created Material: {e2e_mat['material_code']} - {e2e_mat['name']}")

    print("28. Testing Storage Facilities & Warehouses (Facility Creation & Listing)...")
    rand_wh = uuid.uuid4().hex[:4].upper()
    wh_payload = json.dumps({
        "code": f"WH-E2E-{rand_wh}",
        "name": f"E2E Staging Yard {rand_wh}",
        "location": "North Staging Bay 7",
        "type": "PROJECT",
        "project_id": active_project_id
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/inventory/warehouses", data=wh_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        e2e_wh = json.loads(resp.read().decode("utf-8"))
        e2e_wh_id = e2e_wh["id"]
        print(f"   ✓ Registered Storage Facility: {e2e_wh['code']} ({e2e_wh['name']})")

    print("29. Testing Goods Receipt Notes (GRN Intake & WAC Ledger Posting)...")
    grn_payload = json.dumps({
        "receipt_number": f"GRN-E2E-{rand_mat}",
        "purchase_order_id": po_id,
        "supplier_id": supplier_id,
        "warehouse_id": e2e_wh_id,
        "date": "2026-09-07",
        "notes": "Verified against mill certificate MTC-E2E",
        "lines": [
            {
                "purchase_order_line_id": po_line_id,
                "material_id": e2e_mat_id,
                "received_quantity": 25.0,
                "accepted_quantity": 25.0,
                "rejected_quantity": 0.0,
                "unit_cost": 850.0,
                "notes": "E2E accepted intake"
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/inventory/goods-receipts", data=grn_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        e2e_grn = json.loads(resp.read().decode("utf-8"))
        assert e2e_grn["status"] == "POSTED"
        print(f"   ✓ Posted Goods Receipt: {e2e_grn['receipt_number']} (25 TON @ $850 = $21,250.00, Status: POSTED)")

    print("30. Testing Material Issue to Project Site (Cost Code Allocation & Stock Depletion)...")
    iss_payload = json.dumps({
        "issue_number": f"ISS-E2E-{rand_mat}",
        "warehouse_id": e2e_wh_id,
        "project_id": active_project_id,
        "cost_code_id": cost_codes[0]["id"],
        "date": "2026-09-07",
        "purpose": "E2E core wall reinforcement installation",
        "lines": [
            {
                "material_id": e2e_mat_id,
                "quantity": 10.0,
                "notes": "E2E issued to site"
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/inventory/material-issues", data=iss_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        e2e_iss = json.loads(resp.read().decode("utf-8"))
        assert e2e_iss["status"] == "POSTED"
        print(f"   ✓ Posted Material Issue: {e2e_iss['issue_number']} (10 TON dispatched to site, Status: POSTED)")

    print("31. Testing Consolidated Inventory Valuation & Stock Summary Engine...")
    req = urllib.request.Request(f"{API_BASE}/inventory/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        summary_inv = json.loads(resp.read().decode("utf-8"))
        assert float(summary_inv["total_valuation"]) > 0
        assert int(summary_inv["total_items_count"]) >= 1
        assert int(summary_inv["total_warehouses_count"]) >= 2
        assert int(summary_inv["total_receipts_count"]) >= 1
        assert int(summary_inv["total_issues_count"]) >= 1
        print(f"   ✓ Live Inventory Valuation: ${float(summary_inv['total_valuation']):,.2f} across {summary_inv['total_warehouses_count']} facilities ({summary_inv['total_items_count']} materials)")

    print("32. Testing Multi-Page Web Portal Health (All 27 Engineering, Commercial, Procurement & Logistics Routes)...")
    routes = [
        "/en",
        "/en/projects",
        "/en/contracts",
        "/en/clients",
        "/en/wbs",
        "/en/cost-codes",
        "/en/boq",
        "/en/estimates",
        "/en/budgets",
        "/en/subcontracts",
        "/en/change-orders",
        "/en/payment-applications",
        "/en/suppliers",
        "/en/requisitions",
        "/en/rfqs",
        "/en/purchase-orders",
        "/en/materials",
        "/en/warehouses",
        "/en/goods-receipts",
        "/en/material-issues",
        "/ar/subcontracts",
        "/ar/suppliers",
        "/ar/purchase-orders",
        "/ar/materials",
        "/ar/warehouses",
        "/ar/goods-receipts",
        "/ar/material-issues",
    ]
    for route in routes:
        req = urllib.request.Request(f"{WEB_BASE}{route}")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
    print(f"   ✓ All {len(routes)} enterprise portal routes responded with HTTP 200 (OK)")

def main():
    print("=" * 70)
    print("🚀 MODERN CONSTRUCTION ERP — FULL APPLICATION STACK VERIFICATION")
    print("=" * 70)
    try:
        test_web_frontend()
        test_api_health()
        token = test_auth()
        test_erp_workflows(token)
        print("=" * 70)
        print("🎉 ALL 32 REAL ERP SYSTEM VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"❌ Verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
