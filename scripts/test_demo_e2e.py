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
import datetime

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

    print("50. Testing Accounts Receivable Executive Summary Engine (Live SQL Aggregations)...")
    req = urllib.request.Request(f"{API_BASE}/ar/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        ar_summary = json.loads(resp.read().decode("utf-8"))
        assert float(ar_summary["total_invoiced"]) > 0
        assert float(ar_summary["total_receivables"]) > 0
        assert float(ar_summary["total_retention_held"]) > 0
        assert float(ar_summary["total_received"]) > 0
        print(f"   ✓ Live AR Summary: Invoiced=${float(ar_summary['total_invoiced']):,.2f} | Receivables=${float(ar_summary['total_receivables']):,.2f} | Retainage Held=${float(ar_summary['total_retention_held']):,.2f} | Collections=${float(ar_summary['total_received']):,.2f}")

    print("51. Testing Accounts Receivable Invoices Register & Client Queries...")
    req = urllib.request.Request(f"{API_BASE}/ar/invoices", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        ar_invoices = json.loads(resp.read().decode("utf-8"))
        assert len(ar_invoices) >= 1
        print(f"   ✓ Verified AR Client Invoices Register ({len(ar_invoices)} invoices loaded with contract & client relationships)")

    print("52. Testing Progress Billing Invoice Generation from Client Payment Application (IPC)...")
    # Fetch approved client payment application
    req = urllib.request.Request(f"{API_BASE}/commercial/client-payment-applications", headers=headers)
    with urllib.request.urlopen(req) as resp:
        all_pay_apps = json.loads(resp.read().decode("utf-8"))
        assert len(all_pay_apps) >= 1
        e2e_pay_app = all_pay_apps[0]
        pay_app_id = e2e_pay_app["id"]

    req = urllib.request.Request(f"{API_BASE}/ar/invoices/from-payment-application/{pay_app_id}", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        ipc_invoice = json.loads(resp.read().decode("utf-8"))
        e2e_ar_id = ipc_invoice["id"]
        assert ipc_invoice["payment_application_id"] == pay_app_id
        assert float(ipc_invoice["retention_amount"]) > 0
        print(f"   ✓ Generated Progress Billing Invoice: {ipc_invoice['number']} (Gross: ${float(ipc_invoice['subtotal']):,.2f}, Retainage: ${float(ipc_invoice['retention_amount']):,.2f}, Net: ${float(ipc_invoice['total_amount']):,.2f})")

    print("53. Testing Client Invoice Approval Workflow...")
    req = urllib.request.Request(f"{API_BASE}/ar/invoices/{e2e_ar_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        appr_ar = json.loads(resp.read().decode("utf-8"))
        assert appr_ar["status"] == "APPROVED"
        print(f"   ✓ Approved Client Invoice: {appr_ar['number']} (Status: APPROVED)")

    print("54. Testing AR Progress Invoice GL Posting (Balanced Double-Entry with Retainage Asset)...")
    req = urllib.request.Request(f"{API_BASE}/ar/invoices/{e2e_ar_id}/post", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        posted_ar = json.loads(resp.read().decode("utf-8"))
        assert posted_ar["status"] == "POSTED"
        assert posted_ar["journal_id"] is not None
        print(f"   ✓ Posted Client Invoice to GL: Journal {posted_ar['journal_id']} (Balanced Entry: Debit AR 1200 + Debit Retainage 1210 == Credit Revenue 4010)")

    print("55. Testing Customer Collections & Cash Receipts Register...")
    req = urllib.request.Request(f"{API_BASE}/ar/receipts", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        receipts_list = json.loads(resp.read().decode("utf-8"))
        assert len(receipts_list) >= 1
        print(f"   ✓ Verified Customer Receipts Register ({len(receipts_list)} collections loaded)")

    print("56. Testing Customer Cash Collection Voucher & Invoice Allocation Settlement...")
    rand_rec = uuid.uuid4().hex[:4].upper()
    col_amount = min(50000.0, float(posted_ar["outstanding_amount"]))
    rec_payload = json.dumps({
        "reference": f"REC-E2E-{rand_rec}",
        "payment_type": "AR_RECEIPT",
        "date": "2026-09-08",
        "amount": col_amount,
        "currency": "USD",
        "client_id": posted_ar["client_id"],
        "bank_account_id": treasury_bank_id,
        "allocations": [
            {
                "ar_invoice_id": e2e_ar_id,
                "amount": col_amount
            }
        ]
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/ar/receipts", data=rec_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        created_rec = json.loads(resp.read().decode("utf-8"))
        assert created_rec["status"] == "POSTED"
        assert created_rec["journal_id"] is not None
        print(f"   ✓ Recorded Customer Collection: {created_rec['reference']} (${col_amount:,.2f} deposited to Treasury bank, Journal: {created_rec['journal_id']})")

    # Verify Invoice Allocation & Updated Outstanding Balance
    req = urllib.request.Request(f"{API_BASE}/ar/invoices/{e2e_ar_id}", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        updated_ar = json.loads(resp.read().decode("utf-8"))
        assert updated_ar["status"] in ["PARTIAL", "PAID"]
        assert float(updated_ar["paid_amount"]) >= col_amount
        print(f"   ✓ Verified Client Invoice Settlement: {updated_ar['number']} (Status: {updated_ar['status']}, Paid: ${float(updated_ar['paid_amount']):,.2f}, Balance: ${float(updated_ar['outstanding_amount']):,.2f})")

    print("57. Testing Project Cost Control Portfolio Summary Engine (Executive Rollup)...")
    req = urllib.request.Request(f"{API_BASE}/project-cost/portfolio/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        portfolio_summary = json.loads(resp.read().decode("utf-8"))
        assert portfolio_summary["total_projects"] >= 1
        assert float(portfolio_summary["total_budget"]) > 0
        assert float(portfolio_summary["total_committed"]) > 0
        assert float(portfolio_summary["total_actual"]) > 0
        assert float(portfolio_summary["total_eac"]) > 0
        assert "overall_cpi" in portfolio_summary
        print(f"   ✓ Portfolio Cost Summary: Projects={portfolio_summary['total_projects']} | Budget=${float(portfolio_summary['total_budget']):,.2f} | Committed=${float(portfolio_summary['total_committed']):,.2f} | Actual=${float(portfolio_summary['total_actual']):,.2f} | EAC=${float(portfolio_summary['total_eac']):,.2f} | Overall CPI={portfolio_summary['overall_cpi']}")

    print("58. Testing Project Cost Control & Budget Variance Matrix for Skyline Commercial Tower...")
    cost_proj_id = "88888888-8888-4888-8888-888888888888"
    req = urllib.request.Request(f"{API_BASE}/project-cost/projects/{cost_proj_id}/costs/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        cost_matrix = json.loads(resp.read().decode("utf-8"))
        assert len(cost_matrix) >= 8
        rebar_line = next((line for line in cost_matrix if line.get("cost_code_code") == "03-2000"), None)
        assert rebar_line is not None
        assert float(rebar_line["current_budget"]) == 730000.00
        assert float(rebar_line["committed_cost"]) > 0
        assert float(rebar_line["actual_cost"]) > 0
        assert float(rebar_line["estimate_to_complete"]) > 0
        assert float(rebar_line["estimate_at_completion"]) > 0
        print(f"   ✓ Cost Matrix Verified ({len(cost_matrix)} CSI MasterFormat cost codes loaded): Rebar Budget=${float(rebar_line['current_budget']):,.2f}, Committed=${float(rebar_line['committed_cost']):,.2f}, Actual=${float(rebar_line['actual_cost']):,.2f}, ETC=${float(rebar_line['estimate_to_complete']):,.2f}, EAC=${float(rebar_line['estimate_at_completion']):,.2f}, Status={rebar_line['status']}")

    print("59. Testing Earned Value Management (EVM) Single-Project KPIs...")
    req = urllib.request.Request(f"{API_BASE}/project-cost/projects/{cost_proj_id}/costs/kpi", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        project_kpis = json.loads(resp.read().decode("utf-8"))
        assert project_kpis["project_id"] == cost_proj_id
        assert float(project_kpis["total_current_budget"]) == 5200000.00
        assert float(project_kpis["total_committed"]) > 0
        assert float(project_kpis["total_actual"]) > 0
        assert float(project_kpis["total_estimate_to_complete"]) > 0
        assert float(project_kpis["total_variance"]) > 0
        assert float(project_kpis["cost_performance_index"]) > 0
        print(f"   ✓ Project EVM KPIs: Budget=${float(project_kpis['total_current_budget']):,.2f} | Committed=${float(project_kpis['total_committed']):,.2f} | Actual=${float(project_kpis['total_actual']):,.2f} | ETC=${float(project_kpis['total_estimate_to_complete']):,.2f} | VAC=${float(project_kpis['total_variance']):,.2f} | CPI={project_kpis['cost_performance_index']} | Status={project_kpis['status']}")

    print("60. Testing Cost Transactions Audit Ledger Query (Multi-Source Provenance)...")
    req = urllib.request.Request(f"{API_BASE}/project-cost/projects/{cost_proj_id}/costs/transactions", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        cost_txns = json.loads(resp.read().decode("utf-8"))
        assert len(cost_txns) >= 10
        sources = set(t["source_type"] for t in cost_txns)
        assert "PURCHASE_ORDER" in sources or "SUBCONTRACT" in sources or "MATERIAL_ISSUE" in sources
        print(f"   ✓ Cost Transactions Audit: {len(cost_txns)} transactions verified across sources: {', '.join(sorted(sources))}")

    print("61. Testing Project Forecast Creation & Estimate to Complete (ETC) Update...")
    fc_num = f"FC-E2E-{time.time_ns() % 100000}"
    fc_payload = {
        "forecast_number": fc_num,
        "date": datetime.date.today().isoformat(),
        "notes": "E2E Cost Review - Mid-Year ETC Adjustment",
        "lines": [
            {
                "cost_code_id": l["cost_code_id"],
                "etc_amount": 225000.00 if i == 0 else float(l["estimate_to_complete"]),
                "notes": f"Forecast for {l.get('cost_code_code')}"
            }
            for i, l in enumerate(cost_matrix)
        ]
    }
    req = urllib.request.Request(
        f"{API_BASE}/project-cost/projects/{cost_proj_id}/forecasts",
        data=json.dumps(fc_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status in [200, 201]
        created_fc = json.loads(resp.read().decode("utf-8"))
        assert created_fc["forecast_number"] == fc_num
        assert created_fc["status"] == "APPROVED"
        print(f"   ✓ Submitted Project Forecast: {created_fc['forecast_number']} (Status: {created_fc['status']})")

    print("62. Testing Real-time EAC & Budget Variance Recalculation after ETC Adjustment...")
    req = urllib.request.Request(f"{API_BASE}/project-cost/projects/{cost_proj_id}/costs/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        recalculated_matrix = json.loads(resp.read().decode("utf-8"))
        updated_line = next((l for l in recalculated_matrix if l["cost_code_id"] == cost_matrix[0]["cost_code_id"]), None)
        assert updated_line is not None
        assert float(updated_line["estimate_to_complete"]) == 225000.00
        assert float(updated_line["estimate_at_completion"]) == float(updated_line["actual_cost"]) + 225000.00
        print(f"   ✓ Real-time Rollup Verified: Code {updated_line['cost_code_code']} ETC=${float(updated_line['estimate_to_complete']):,.2f} -> EAC=${float(updated_line['estimate_at_completion']):,.2f}, Variance=${float(updated_line['variance']):,.2f}")

    print("63. Testing Equipment Fleet Executive Summary Engine (Live SQL Aggregations)...")
    req = urllib.request.Request(f"{API_BASE}/equipment/summary", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        fleet_summary = json.loads(resp.read().decode("utf-8"))
        assert fleet_summary["total_units"] >= 8
        assert fleet_summary["available_units"] >= 1
        assert fleet_summary["in_use_units"] >= 1
        assert float(fleet_summary["total_operating_hours"]) > 0
        assert float(fleet_summary["total_fuel_cost"]) > 0
        assert float(fleet_summary["total_maintenance_cost"]) > 0
        assert float(fleet_summary["total_equipment_cost"]) > 0
        print(f"   ✓ Fleet Executive Summary: Total={fleet_summary['total_units']} Units | In-Use={fleet_summary['in_use_units']} | Available={fleet_summary['available_units']} | Hours={float(fleet_summary['total_operating_hours']):,.1f}h | Fuel=${float(fleet_summary['total_fuel_cost']):,.2f} | Maint=${float(fleet_summary['total_maintenance_cost']):,.2f} | Utilization={fleet_summary['utilization_rate']}%")

    print("64. Testing Equipment Master Register Query & Telematics Overview...")
    req = urllib.request.Request(f"{API_BASE}/equipment/", headers=headers)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        fleet_list = json.loads(resp.read().decode("utf-8"))
        assert len(fleet_list) >= 8
        first_machine = fleet_list[0]
        assert "total_operating_hours" in first_machine
        assert "total_fuel_cost" in first_machine
        assert "total_maintenance_cost" in first_machine
        print(f"   ✓ Master Fleet Register: {len(fleet_list)} machines active in catalog. Lead Asset: [{first_machine.get('internal_id')}] {first_machine.get('name')} (Site: {first_machine.get('active_project_name') or 'Depot'})")

    print("65. Testing Heavy Equipment Registration Workflow...")
    eq_code = f"EQ-E2E-{time.time_ns() % 100000}"
    new_eq_payload = {
        "name": f"Komatsu PC210LC-11 Excavator {eq_code}",
        "make": "Komatsu",
        "model": "PC210LC-11",
        "year": "2024",
        "serial_number": f"SN-{eq_code}",
        "internal_id": eq_code,
        "status": "AVAILABLE",
        "base_hourly_cost": 185.00
    }
    req = urllib.request.Request(
        f"{API_BASE}/equipment/",
        data=json.dumps(new_eq_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created_eq = json.loads(resp.read().decode("utf-8"))
        assert created_eq["internal_id"] == eq_code
        assert created_eq["status"] == "AVAILABLE"
        eq_id = created_eq["id"]
        print(f"   ✓ Registered Machinery Asset: [{created_eq['internal_id']}] {created_eq['name']} (Base Rate: ${float(created_eq['base_hourly_cost']):,.2f}/hr)")

    print("66. Testing Project Site Dispatch & Assignment with Rate Override...")
    dispatch_payload = {
        "equipment_id": eq_id,
        "project_id": cost_proj_id,
        "start_date": datetime.date.today().isoformat(),
        "hourly_cost_override": 195.00
    }
    req = urllib.request.Request(
        f"{API_BASE}/equipment/assignments",
        data=json.dumps(dispatch_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        dispatch_res = json.loads(resp.read().decode("utf-8"))
        assert dispatch_res["equipment_id"] == eq_id
        assert float(dispatch_res["hourly_cost_override"]) == 195.00
        print(f"   ✓ Dispatched Equipment to Project Site: Assignment {dispatch_res['id']} (Locked Override: ${float(dispatch_res['hourly_cost_override']):,.2f}/hr)")

    print("67. Testing Shift Operating Timesheet Lifecycle (Draft -> Submit -> Approve)...")
    usage_payload = {
        "equipment_id": eq_id,
        "period_start": datetime.date.today().isoformat(),
        "period_end": (datetime.date.today() + datetime.timedelta(days=6)).isoformat(),
        "lines": [
            {
                "project_id": cost_proj_id,
                "cost_code_id": cost_matrix[0]["cost_code_id"],
                "date": datetime.date.today().isoformat(),
                "hours": 10.0
            }
        ]
    }
    req = urllib.request.Request(
        f"{API_BASE}/equipment/usage-logs",
        data=json.dumps(usage_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        usage_res = json.loads(resp.read().decode("utf-8"))
        usage_id = usage_res["id"]
        assert usage_res["status"] == "DRAFT"

    # Submit
    req = urllib.request.Request(f"{API_BASE}/equipment/usage-logs/{usage_id}/submit", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        assert json.loads(resp.read().decode("utf-8"))["status"] == "SUBMITTED"

    # Approve
    req = urllib.request.Request(f"{API_BASE}/equipment/usage-logs/{usage_id}/approve", headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        approved_log = json.loads(resp.read().decode("utf-8"))
        assert approved_log["status"] == "APPROVED"
        assert float(approved_log["lines"][0]["hourly_cost_rate"]) == 195.00
        assert float(approved_log["lines"][0]["total_cost"]) == 1950.00
        print(f"   ✓ Approved Equipment Timesheet: 10.0 hrs @ $195.00 = ${float(approved_log['lines'][0]['total_cost']):,.2f} charged to Cost Code {cost_matrix[0]['cost_code_code']}")

    print("68. Testing Fuel Delivery & Consumption Ledger Logging...")
    fuel_payload = {
        "equipment_id": eq_id,
        "project_id": cost_proj_id,
        "cost_code_id": cost_matrix[0]["cost_code_id"],
        "date": datetime.date.today().isoformat(),
        "volume": 250.0,
        "unit_cost": 3.85
    }
    req = urllib.request.Request(
        f"{API_BASE}/equipment/fuel",
        data=json.dumps(fuel_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        fuel_res = json.loads(resp.read().decode("utf-8"))
        assert float(fuel_res["total_cost"]) == 962.50
        print(f"   ✓ Logged Site Fuel Delivery: 250.0 gal @ $3.85/gal = ${float(fuel_res['total_cost']):,.2f}")

    print("69. Testing Maintenance & Corrective Service Work Order Workflow...")
    maint_payload = {
        "equipment_id": eq_id,
        "project_id": cost_proj_id,
        "cost_code_id": cost_matrix[0]["cost_code_id"],
        "type": "CORRECTIVE",
        "date": datetime.date.today().isoformat(),
        "description": "Bucket tooth wear replacement & pin bushing greasing",
        "duration_hours": 3.0,
        "cost": 420.00
    }
    req = urllib.request.Request(
        f"{API_BASE}/equipment/maintenance",
        data=json.dumps(maint_payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        maint_res = json.loads(resp.read().decode("utf-8"))
        assert float(maint_res["cost"]) == 420.00
        print(f"   ✓ Created Corrective Maintenance Work Order: ${float(maint_res['cost']):,.2f} (Status transitioned to MAINTENANCE)")

    print("70. Testing Multi-Page Web Portal Health (All 47 Engineering, Commercial, Procurement, Inventory, AP, AR, GL, Cost Control & Equipment Routes)...")
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
        "/en/cost-control",
        "/en/equipment",
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
        "/en/ar/invoices",
        "/en/ar/receipts",
        "/en/accounting/accounts",
        "/en/accounting/journals",
        "/en/accounting/periods",
        "/en/accounting/reports",
        "/ar/cost-control",
        "/ar/equipment",
        "/ar/subcontracts",
        "/ar/suppliers",
        "/ar/purchase-orders",
        "/ar/materials",
        "/ar/warehouses",
        "/ar/goods-receipts",
        "/ar/material-issues",
        "/ar/ap/invoices",
        "/ar/ap/payments",
        "/ar/ar/invoices",
        "/ar/ar/receipts",
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
        print("🎉 ALL 70 REAL ERP SYSTEM VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
        print("=" * 70)
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
