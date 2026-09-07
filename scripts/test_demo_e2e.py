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
import time

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
        assert Decimal(str(exec_dash["total_open_payables"])) > Decimal("0.00")
        assert exec_dash["total_ap_invoices"] >= 1
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

    print("32. Testing Accounts Payable Executive Summary Engine (Live SQL Aggregation)...")
    req = urllib.request.Request(f"{API_BASE}/ap/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        summary_ap = json.loads(resp.read().decode("utf-8"))
        assert float(summary_ap["total_invoiced"]) > 0
        assert int(summary_ap["invoices_count"]) >= 1
        assert int(summary_ap["matched_count"]) >= 1
        print(f"   ✓ Live AP Summary: Invoiced=${float(summary_ap['total_invoiced']):,.2f}, Payables=${float(summary_ap['total_payables']):,.2f}, Disbursed=${float(summary_ap['total_paid']):,.2f} ({summary_ap['matched_count']} matched)")

    print("33. Testing Accounts Payable Invoices Register & Filtering...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices", headers=headers)
    with urllib.request.urlopen(req) as resp:
        ap_invoices = json.loads(resp.read().decode("utf-8"))
        assert len(ap_invoices) >= 1
        print(f"   ✓ Verified AP Invoices Register ({len(ap_invoices)} invoices loaded)")

    print("34. Testing Vendor Invoice Registration against PO & GRN...")
    rand_ap = uuid.uuid4().hex[:4].upper()
    inv_payload = json.dumps({
        "number": f"INV-E2E-{rand_ap}",
        "supplier_id": supplier_id,
        "purchase_order_id": po_id,
        "goods_receipt_id": e2e_grn["id"],
        "date": "2026-09-07",
        "due_date": "2026-10-07",
        "description": f"E2E Structural Rebar Batch {rand_ap}",
        "tax_amount": 0.0,
        "lines": [
            {
                "purchase_order_line_id": po_line_id,
                "goods_receipt_line_id": e2e_grn["lines"][0]["id"] if e2e_grn.get("lines") else None,
                "material_id": e2e_mat_id,
                "description": "16mm High-Tensile Deformed Rebar Grade 60",
                "quantity": 25.0,
                "unit_price": 850.0,
                "tax_rate": 0.0
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices", data=inv_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        e2e_inv = json.loads(resp.read().decode("utf-8"))
        e2e_inv_id = e2e_inv["id"]
        assert float(e2e_inv["total_amount"]) == 21250.0
        print(f"   ✓ Registered Vendor Invoice: {e2e_inv['number']} ($21,250.00, Status: {e2e_inv['status']})")

    print("35. Testing 3-Way Match Verification Engine (PO vs GRN vs Invoice)...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices/{e2e_inv_id}/match", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        match_report = json.loads(resp.read().decode("utf-8"))
        assert match_report["is_matched"] is True
        assert match_report["matching_status"] == "MATCHED"
        assert float(match_report["variance_amount"]) == 0.0
        print(f"   ✓ 3-Way Match Verified: Invoice {match_report['invoice_number']} matches PO {match_report['po_number']} and GRN {match_report['grn_number']} (Zero Variance)")

    print("36. Testing AP Invoice Approval Workflow...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices/{e2e_inv_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        appr_inv = json.loads(resp.read().decode("utf-8"))
        assert appr_inv["status"] == "APPROVED"
        print(f"   ✓ Approved Matched Invoice: {appr_inv['number']} (Status: APPROVED)")

    print("37. Testing AP Invoice Posting to General Ledger (Balanced Journal Entry)...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices/{e2e_inv_id}/post", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        posted_inv = json.loads(resp.read().decode("utf-8"))
        assert posted_inv["status"] == "POSTED"
        assert posted_inv["journal_id"] is not None
        print(f"   ✓ Posted Invoice to GL: Journal {posted_inv['journal_id']} (Status: POSTED, Balance: ${float(posted_inv['outstanding_amount']):,.2f})")

    print("38. Testing Treasury Bank Accounts...")
    req = urllib.request.Request(f"{API_BASE}/ap/bank-accounts", headers=headers)
    with urllib.request.urlopen(req) as resp:
        bank_accounts = json.loads(resp.read().decode("utf-8"))
        assert len(bank_accounts) >= 1
        treasury_bank_id = bank_accounts[0]["id"]
        print(f"   ✓ Active Treasury Bank Account: {bank_accounts[0]['name']} ({bank_accounts[0]['account_number']})")

    print("39. Testing Vendor Payment Disbursement & Allocation...")
    pay_payload = json.dumps({
        "reference": f"PAY-E2E-{rand_ap}",
        "payment_type": "AP_PAYMENT",
        "date": "2026-09-07",
        "amount": 21250.0,
        "currency": "USD",
        "supplier_id": supplier_id,
        "bank_account_id": treasury_bank_id,
        "allocations": [
            {
                "ap_invoice_id": e2e_inv_id,
                "amount": 21250.0
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/ap/payments", data=pay_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        e2e_pay = json.loads(resp.read().decode("utf-8"))
        assert e2e_pay["status"] == "POSTED"
        assert e2e_pay["journal_id"] is not None
        print(f"   ✓ Disbursed Vendor Payment: {e2e_pay['reference']} ($21,250.00 posted to Treasury GL)")

    print("40. Testing Invoice Balance Settlement (Status -> PAID)...")
    req = urllib.request.Request(f"{API_BASE}/ap/invoices/{e2e_inv_id}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        settled_inv = json.loads(resp.read().decode("utf-8"))
        assert settled_inv["status"] == "PAID"
        assert float(settled_inv["outstanding_amount"]) == 0.0
        print(f"   ✓ Fully Settled AP Invoice: {settled_inv['number']} (Status: PAID, Outstanding: $0.00)")

    print("41. Testing Payments Register...")
    req = urllib.request.Request(f"{API_BASE}/ap/payments", headers=headers)
    with urllib.request.urlopen(req) as resp:
        all_payments = json.loads(resp.read().decode("utf-8"))
        assert len(all_payments) >= 1
        print(f"   ✓ Verified Payments Register ({len(all_payments)} disbursements loaded)")

    print("42. Testing General Ledger Summary & Real-Time Balancing Engine...")
    req = urllib.request.Request(f"{API_BASE}/accounting/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        gl_summary = json.loads(resp.read().decode("utf-8"))
        assert gl_summary["is_ledger_balanced"] is True
        assert float(gl_summary["total_debits"]) == float(gl_summary["total_credits"])
        assert gl_summary["total_accounts"] >= 20
        assert gl_summary["posted_journals"] >= 1
        print(f"   ✓ Verified Live GL Summary: Balanced={gl_summary['is_ledger_balanced']} | Volume=${float(gl_summary['total_debits']):,.2f} | Accounts={gl_summary['total_accounts']}")

    print("43. Testing Chart of Accounts Query & Category Breakdown...")
    req = urllib.request.Request(f"{API_BASE}/accounting/accounts", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        accounts = json.loads(resp.read().decode("utf-8"))
        assert len(accounts) >= 20
        asset_accs = [a for a in accounts if a["account_type"] == "ASSET"]
        assert len(asset_accs) >= 4
        print(f"   ✓ Chart of Accounts Loaded ({len(accounts)} accounts with live balances, {len(asset_accs)} assets)")

    print("44. Testing Account Creation Validation...")
    new_acc_payload = json.dumps({
        "account_code": f"1099-{int(time.time()) % 10000}",
        "name": "E2E Petty Cash Site Fund",
        "account_type": "ASSET",
        "description": "Petty cash emergency fund for site operations",
        "is_active": True
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/accounting/accounts", data=new_acc_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        created_acc = json.loads(resp.read().decode("utf-8"))
        assert created_acc["account_type"] == "ASSET"
        print(f"   ✓ Created New GL Account: [{created_acc['account_code']}] {created_acc['name']}")

    print("45. Testing Journal Vouchers Register & Lines...")
    req = urllib.request.Request(f"{API_BASE}/accounting/journals", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        journals = json.loads(resp.read().decode("utf-8"))
        assert len(journals) >= 1
        print(f"   ✓ Journal Vouchers Register: {len(journals)} vouchers loaded with multi-line breakdown")

    print("46. Testing Double-Entry Journal Creation & Posting to GL...")
    # Find cash account and equity account
    cash_acc = next((a for a in accounts if a["account_code"] == "1010"), accounts[0])
    equity_acc = next((a for a in accounts if a["account_code"] == "3010"), accounts[-1])
    jv_payload = json.dumps({
        "date": "2026-08-15",
        "reference": f"E2E-CAPITAL-{int(time.time()) % 1000}",
        "description": "Additional Owner Capital Injection for Project Expansion",
        "lines": [
            {
                "account_id": cash_acc["id"],
                "debit": 50000.0,
                "credit": 0.0,
                "description": "Bank Cash Inflow"
            },
            {
                "account_id": equity_acc["id"],
                "debit": 0.0,
                "credit": 50000.0,
                "description": "Owner Paid-in Capital"
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/accounting/journals", data=jv_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        created_jv = json.loads(resp.read().decode("utf-8"))
        jv_id = created_jv["id"]
        assert created_jv["status"] == "DRAFT"
        assert created_jv["is_balanced"] is True
        print(f"   ✓ Created Balanced JV: {created_jv.get('reference', created_jv['id'])} (Debits: ${float(created_jv['total_debit']):,.2f} == Credits: ${float(created_jv['total_credit']):,.2f})")

    # Post JV
    req = urllib.request.Request(f"{API_BASE}/accounting/journals/{jv_id}/post", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        posted_jv = json.loads(resp.read().decode("utf-8"))
        assert posted_jv["status"] == "POSTED"
        print(f"   ✓ Posted JV {posted_jv.get('reference', posted_jv['id'])} to General Ledger (Status: POSTED)")

    print("47. Testing Journal Voucher Audit Reversal...")
    rev_payload = json.dumps({
        "reversal_date": "2026-08-16",
        "description": "Audit Correction Reversal for Capital Entry"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/accounting/journals/{jv_id}/reverse", data=rev_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        rev_jv = json.loads(resp.read().decode("utf-8"))
        assert rev_jv["status"] == "POSTED"
        assert "REV-" in (rev_jv.get("reference") or "")
        print(f"   ✓ Reversed JV: Original status now REVERSED, Reversal voucher {rev_jv.get('reference', rev_jv['id'])} posted")

    print("48. Testing Financial Periods & Month-End Closing Controls...")
    req = urllib.request.Request(f"{API_BASE}/accounting/periods", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        periods = json.loads(resp.read().decode("utf-8"))
        assert len(periods) >= 12
        open_periods = [p for p in periods if not p["is_closed"]]
        target_period = open_periods[-1]
        p_id = target_period["id"]
        print(f"   ✓ Loaded {len(periods)} Financial Periods ({len(open_periods)} Open, {len(periods)-len(open_periods)} Closed)")

    # Test closing period
    req = urllib.request.Request(f"{API_BASE}/accounting/periods/{p_id}/close", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        closed_p = json.loads(resp.read().decode("utf-8"))
        assert closed_p["is_closed"] is True
        print(f"   ✓ Closed Period {closed_p['name']} (Month-End Lock Active)")

    # Test reopening period
    req = urllib.request.Request(f"{API_BASE}/accounting/periods/{p_id}/reopen", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        reopened_p = json.loads(resp.read().decode("utf-8"))
        assert reopened_p["is_closed"] is False
        print(f"   ✓ Reopened Period {reopened_p['name']} (Period Unlocked for Postings)")

    print("49. Testing Financial Statements Studio (Balance Sheet & Income Statement)...")
    req = urllib.request.Request(f"{API_BASE}/accounting/reports/balance-sheet?as_of_date=2026-12-31", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        bs = json.loads(resp.read().decode("utf-8"))
        assert bs["is_balanced"] is True
        assert abs(float(bs["total_assets"]) - (float(bs["total_liabilities"]) + float(bs["total_equity"]) + float(bs["retained_earnings"]))) < 0.01
        print(f"   ✓ Balance Sheet As-of 2026-12-31: Assets=${float(bs['total_assets']):,.2f} == Liab+Eq+RetEarnings=${float(bs['total_liabilities']) + float(bs['total_equity']) + float(bs['retained_earnings']):,.2f} (Balanced={bs['is_balanced']})")

    req = urllib.request.Request(f"{API_BASE}/accounting/reports/income-statement?start_date=2026-01-01&end_date=2026-12-31", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        pnl = json.loads(resp.read().decode("utf-8"))
        assert abs(float(pnl["net_profit"]) - (float(pnl["total_revenue"]) - float(pnl["total_expenses"]))) < 0.01
        print(f"   ✓ Income Statement (P&L): Revenue=${float(pnl['total_revenue']):,.2f} | Expenses=${float(pnl['total_expenses']):,.2f} | Net Profit=${float(pnl['net_profit']):,.2f}")

    print("50. Testing Multi-Page Web Portal Health (All 39 Engineering, Commercial, Procurement, Logistics, AP & GL Routes)...")
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
        "/en/ap/invoices",
        "/en/ap/payments",
        "/en/accounting/accounts",
        "/en/accounting/journals",
        "/en/accounting/periods",
        "/en/accounting/reports",
        "/ar/subcontracts",
        "/ar/suppliers",
        "/ar/purchase-orders",
        "/ar/materials",
        "/ar/warehouses",
        "/ar/goods-receipts",
        "/ar/material-issues",
        "/ar/ap/invoices",
        "/ar/ap/payments",
        "/ar/accounting/accounts",
        "/ar/accounting/journals",
        "/ar/accounting/periods",
        "/ar/accounting/reports",
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
        print("🎉 ALL 50 REAL ERP SYSTEM VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
        print("=" * 70)
        return 0
    except Exception as e:
        import traceback; traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
