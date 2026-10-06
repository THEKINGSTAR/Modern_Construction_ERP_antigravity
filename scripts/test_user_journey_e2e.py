#!/usr/bin/env python3
"""
scripts/test_user_journey_e2e.py
Authoritative End-to-End Business Journey Verification Suite for Stage 34.

Verifies the complete real ERP construction transaction lifecycle:
  LOGIN
   ↓
  PROJECT (Create / Select)
   ↓
  PROCUREMENT (Purchase Order)
   ↓
  GOODS RECEIPT (GRN Intake)
   ↓
  INVENTORY (Stock Ledger & Valuation)
   ↓
  MATERIAL ISSUE (Site Dispatch & Cost Allocation)
   ↓
  PROJECT COST (Actual Cost Engine & Audit Ledger)
   ↓
  VENDOR INVOICE (AP Registration)
   ↓
  3-WAY MATCH (PO vs GRN vs Invoice)
   ↓
  AP POSTING (Status POSTED & Outstanding Tracking)
   ↓
  GL BALANCING (Double-Entry Debit == Credit Journal Vouchers)
   ↓
  REPORTING (Project Dashboard, Budget-vs-Actual, Executive KPIs)
   ↓
  INDEPENDENT DATABASE CHECK (Direct PostgreSQL queries on port 5434)
   ↓
  RESTART TEST (Container restart & state persistence validation)
   ↓
  SECURITY TEST (Cross-tenant negative mutation prevention)
"""

import sys
import os
import uuid
import json
import time
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from decimal import Decimal
import psycopg2
from psycopg2.extras import RealDictCursor

API_BASE = "http://localhost:8000/api/v1"
WEB_BASE = "http://localhost:3000"
DB_HOST = "localhost"
DB_PORT = 5434
DB_NAME = "erp"
DB_USER = "postgres"
DB_PASS = "postgres"


def make_request(url: str, method: str = "GET", data: dict = None, headers: dict = None):
    req_headers = headers.copy() if headers else {}
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            parsed = json.loads(err_body)
        except Exception:
            parsed = {"detail": err_body}
        return e.code, parsed


def run_cmd(cmd_list, wait: bool = True):
    res = subprocess.run(cmd_list, capture_output=True, text=True)
    return res.returncode, res.stdout, res.stderr


def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        port=DB_PORT
    )


def main():
    print("======================================================================")
    print("STAGE 34: AUTHORITATIVE ERP PRODUCTIZATION & WORKFLOW HARDENING TEST")
    print("======================================================================")
    run_suffix = uuid.uuid4().hex[:6].upper()
    print(f"Test Run Identifier: STG34-{run_suffix}\n")

    # -------------------------------------------------------------------------
    # STEP 1: Verify Web Portal & Connected Route Availability
    # -------------------------------------------------------------------------
    print("1. Verifying Web Portal & Connected Workflow Routes...")
    test_routes = [
        "/en",
        "/en/projects",
        "/en/purchase-orders",
        "/en/goods-receipts",
        "/en/material-issues",
        "/en/cost-control",
        "/en/ap/invoices",
        "/en/accounting/journals",
        "/en/accounting/reports",
        "/en/reports",
    ]
    for route in test_routes:
        req = urllib.request.Request(f"{WEB_BASE}{route}")
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200, f"Route {route} failed with {resp.status}"
    print(f"   ✓ All {len(test_routes)} core workflow portal routes responded with HTTP 200 OK.")

    # -------------------------------------------------------------------------
    # STEP 2: Authentication
    # -------------------------------------------------------------------------
    print("2. Authenticating ERP User & Obtaining JWT Bearer Token...")
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
        token_data = json.loads(resp.read().decode("utf-8"))
        token = token_data.get("access_token")
        assert token, "Login failed: No access_token returned"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print("   ✓ User authenticated successfully. JWT session token acquired.")

    # -------------------------------------------------------------------------
    # STEP 3: Create Project
    # -------------------------------------------------------------------------
    print("3. Creating Active Construction Project...")
    proj_code = f"PRJ-STG34-{run_suffix}"
    proj_name = f"Coastal Pier & Terminal Phase {run_suffix}"
    status, proj_data = make_request(
        f"{API_BASE}/projects/",
        method="POST",
        headers=headers,
        data={
            "project_number": proj_code,
            "name": proj_name,
            "project_type": "Infrastructure",
            "budget_amount": "4500000.00",
            "status": "ACTIVE"
        }
    )
    assert status == 201, f"Failed to create project: {proj_data}"
    project_id = proj_data["id"]
    print(f"   ✓ Created Project: {proj_name} [{proj_code}] (ID: {project_id})")

    # -------------------------------------------------------------------------
    # STEP 4: Setup Supporting Entities (Supplier, Material, Warehouse, Cost Code)
    # -------------------------------------------------------------------------
    print("4. Resolving Supplier, Material Catalog, Storage Yard, and Cost Code...")
    # Get or create supplier
    status, suppliers = make_request(f"{API_BASE}/suppliers/", headers=headers)
    assert status == 200 and len(suppliers) > 0, "No suppliers found"
    supplier_id = suppliers[0]["id"]
    supplier_name = suppliers[0]["name"]

    # Create distinct Material Master item
    mat_code = f"MAT-STG34-{run_suffix}"
    status, mat_data = make_request(
        f"{API_BASE}/inventory/materials",
        method="POST",
        headers=headers,
        data={
            "material_code": mat_code,
            "name": f"High-Tensile Rebar STG34 {run_suffix}",
            "description": "Grade 60 structural deformed bar",
            "category": "Metals & Rebar",
            "base_unit": "TON"
        }
    )
    assert status in [200, 201], f"Failed to create material: {mat_data}"
    material_id = mat_data["id"]

    # Create distinct Warehouse / Storage Facility
    wh_code = f"WH-STG34-{run_suffix}"
    status, wh_data = make_request(
        f"{API_BASE}/inventory/warehouses",
        method="POST",
        headers=headers,
        data={
            "code": wh_code,
            "name": f"Harbor Staging Yard {run_suffix}",
            "location": "North Dock Gate 4",
            "type": "CENTRAL"
        }
    )
    assert status in [200, 201], f"Failed to create warehouse: {wh_data}"
    warehouse_id = wh_data["id"]

    # Get CSI Cost Code
    status, cost_codes = make_request(f"{API_BASE}/cost-codes", headers=headers)
    assert status == 200 and len(cost_codes) > 0, "No cost codes found"
    cost_code = cost_codes[0]
    cost_code_id = cost_code["id"]
    print(f"   ✓ Supplier: {supplier_name} | Material: {mat_code} | Warehouse: {wh_code} | Cost Code: {cost_code.get('code')}")

    # -------------------------------------------------------------------------
    # STEP 5: Create and Issue Purchase Order
    # -------------------------------------------------------------------------
    print("5. Creating and Issuing Purchase Order (Procurement)...")
    po_number = f"PO-STG34-{run_suffix}"
    status, po_data = make_request(
        f"{API_BASE}/purchase-orders/",
        method="POST",
        headers=headers,
        data={
            "po_number": po_number,
            "supplier_id": supplier_id,
            "project_id": project_id,
            "currency": "USD",
            "total_amount": 50000.0,
            "lines": [
                {
                    "item_description": f"Grade 60 Structural Rebar {run_suffix}",
                    "cost_code_id": cost_code_id,
                    "unit": "TON",
                    "quantity": 100.0,
                    "unit_price": 500.0,
                    "amount": 50000.0
                }
            ]
        }
    )
    assert status in [200, 201], f"Failed to create PO: {po_data}"
    po_id = po_data["id"]
    po_line_id = po_data["lines"][0]["id"]
    assert float(po_data["total_amount"]) == 50000.0

    # Issue PO
    status, issued_po = make_request(
        f"{API_BASE}/purchase-orders/{po_id}/issue",
        method="POST",
        headers=headers
    )
    assert status == 200 and issued_po.get("status") == "success", f"Failed to issue PO: {issued_po}"
    status, po_verify = make_request(f"{API_BASE}/purchase-orders/{po_id}", headers=headers)
    assert status == 200 and po_verify["status"] == "ISSUED"
    print(f"   ✓ Created and Issued PO: {po_number} (100 TON @ $500 = $50,000.00, Status: ISSUED)")

    # -------------------------------------------------------------------------
    # STEP 6: Verify Committed Cost in Project Cost Engine
    # -------------------------------------------------------------------------
    print("6. Verifying Committed Cost Propagation in Project Cost Engine...")
    status, cost_summary = make_request(
        f"{API_BASE}/project-cost/projects/{project_id}/costs/kpi",
        headers=headers
    )
    assert status == 200
    committed = float(cost_summary.get("total_committed", 0))
    assert committed == 50000.0, f"Expected committed cost 50000.0, got {committed}"
    print(f"   ✓ Project Cost Engine correctly captured committed cost: ${committed:,.2f}")

    # -------------------------------------------------------------------------
    # STEP 7: Receive Goods via Goods Receipt Note (GRN)
    # -------------------------------------------------------------------------
    print("7. Receiving Physical Material via Goods Receipt Note (GRN Intake)...")
    grn_number = f"GRN-STG34-{run_suffix}"
    status, grn_data = make_request(
        f"{API_BASE}/inventory/goods-receipts",
        method="POST",
        headers=headers,
        data={
            "receipt_number": grn_number,
            "purchase_order_id": po_id,
            "supplier_id": supplier_id,
            "warehouse_id": warehouse_id,
            "date": "2026-09-08",
            "notes": f"Stage 34 Intake - Mill Test Cert Validated",
            "lines": [
                {
                    "purchase_order_line_id": po_line_id,
                    "material_id": material_id,
                    "received_quantity": 100.0,
                    "accepted_quantity": 100.0,
                    "rejected_quantity": 0.0,
                    "unit_cost": 500.0,
                    "notes": "Full shipment accepted"
                }
            ]
        }
    )
    assert status in [200, 201], f"Failed to record GRN: {grn_data}"
    grn_id = grn_data["id"]
    grn_line_id = grn_data["lines"][0]["id"]
    assert grn_data["status"] == "POSTED"
    print(f"   ✓ Posted GRN: {grn_number} (Received 100 TON into {wh_code}, Status: POSTED)")

    # -------------------------------------------------------------------------
    # STEP 8: Verify Inventory Stock Balance
    # -------------------------------------------------------------------------
    print("8. Verifying Warehouse Stock Ledger & Valuation...")
    status, balances = make_request(f"{API_BASE}/inventory/balances", headers=headers)
    assert status == 200
    wh_bal = next(
        (b for b in balances if b["warehouse_id"] == warehouse_id and b["material_id"] == material_id),
        None
    )
    assert wh_bal is not None, f"Balance record not found for warehouse {warehouse_id}"
    assert float(wh_bal["quantity"]) == 100.0, f"Expected 100 TON in stock, got {wh_bal['quantity']}"
    assert float(wh_bal["total_cost"]) == 50000.0
    print(f"   ✓ Warehouse Inventory verified: {wh_bal['quantity']} TON on hand (Valuation: ${float(wh_bal['total_cost']):,.2f})")

    # -------------------------------------------------------------------------
    # STEP 9: Issue Material to Project Site (With Negative Test for Over-Issue)
    # -------------------------------------------------------------------------
    print("9. Testing Material Issue to Project Site & Stock Validation...")
    # Over-issue negative test: try to issue 150 TON when only 100 TON is available
    status_over, res_over = make_request(
        f"{API_BASE}/inventory/material-issues",
        method="POST",
        headers=headers,
        data={
            "issue_number": f"ISS-FAIL-{run_suffix}",
            "warehouse_id": warehouse_id,
            "project_id": project_id,
            "cost_code_id": cost_code_id,
            "date": "2026-09-08",
            "purpose": "Excessive dispatch test",
            "lines": [
                {
                    "material_id": material_id,
                    "quantity": 150.0,
                    "notes": "Should be rejected"
                }
            ]
        }
    )
    assert status_over == 400, f"Expected 400 for over-issue, got {status_over}"
    print(f"   ✓ Over-issue validation passed: Rejected 150 TON request exceeding 100 TON balance (HTTP 400).")

    # Valid Issue: 40 TON to Site
    iss_number = f"ISS-STG34-{run_suffix}"
    status, iss_data = make_request(
        f"{API_BASE}/inventory/material-issues",
        method="POST",
        headers=headers,
        data={
            "issue_number": iss_number,
            "warehouse_id": warehouse_id,
            "project_id": project_id,
            "cost_code_id": cost_code_id,
            "date": "2026-09-08",
            "purpose": "Substructure Pier Foundation Reinforcement",
            "lines": [
                {
                    "material_id": material_id,
                    "quantity": 40.0,
                    "notes": "Dispatched to site foundation"
                }
            ]
        }
    )
    assert status in [200, 201], f"Failed to issue material: {iss_data}"
    issue_id = iss_data["id"]
    assert iss_data["status"] == "POSTED"
    print(f"   ✓ Posted Material Issue: {iss_number} (40 TON @ $500 = $20,000.00 to Project)")

    # Verify inventory was depleted by 40 TON -> 60 TON remaining
    status, balances_after = make_request(f"{API_BASE}/inventory/balances", headers=headers)
    assert status == 200
    wh_bal_after = next(
        (b for b in balances_after if b["warehouse_id"] == warehouse_id and b["material_id"] == material_id),
        None
    )
    assert wh_bal_after is not None
    assert float(wh_bal_after["quantity"]) == 60.0, f"Expected 60 TON remaining, got {wh_bal_after['quantity']}"
    print(f"   ✓ Warehouse balance accurately depleted: 60 TON remaining (Valuation: ${float(wh_bal_after['total_cost']):,.2f})")

    # -------------------------------------------------------------------------
    # STEP 10: Verify Project Cost Engine Actual Cost Propagation
    # -------------------------------------------------------------------------
    print("10. Verifying Project Cost Engine & Cost Transactions Ledger...")
    status, cost_summary_after = make_request(
        f"{API_BASE}/project-cost/projects/{project_id}/costs/kpi",
        headers=headers
    )
    assert status == 200
    actual_cost = float(cost_summary_after.get("total_actual", 0))
    assert actual_cost == 20000.0, f"Expected actual cost $20,000.00, got ${actual_cost}"
    print(f"   ✓ Project Cost Engine correctly updated Actual Cost: ${actual_cost:,.2f}")

    # Verify audit transaction ledger provenance
    status, txns = make_request(
        f"{API_BASE}/project-cost/projects/{project_id}/costs/transactions",
        headers=headers
    )
    assert status == 200
    matching_txn = next(
        (t for t in txns if t["source_type"] == "MATERIAL_ISSUE" and t.get("source_reference") == iss_number),
        None
    )
    assert matching_txn is not None, f"Cost transaction for issue {iss_number} not found in ledger"
    assert float(matching_txn["amount"]) == 20000.0
    print(f"   ✓ Cost Transactions Audit Ledger contains verified record: {matching_txn['source_reference']} (${float(matching_txn['amount']):,.2f}, Type: {matching_txn['cost_type']})")

    # -------------------------------------------------------------------------
    # STEP 11: Register Vendor Invoice (AP)
    # -------------------------------------------------------------------------
    print("11. Registering Vendor Invoice linked to PO and GRN (Accounts Payable)...")
    inv_number = f"INV-STG34-{run_suffix}"
    status, inv_data = make_request(
        f"{API_BASE}/ap/invoices",
        method="POST",
        headers=headers,
        data={
            "number": inv_number,
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "goods_receipt_id": grn_id,
            "date": "2026-09-08",
            "due_date": "2026-10-08",
            "description": f"Invoice for Structural Rebar {run_suffix}",
            "tax_amount": 0.0,
            "lines": [
                {
                    "purchase_order_line_id": po_line_id,
                    "goods_receipt_line_id": grn_line_id,
                    "material_id": material_id,
                    "description": f"100 TON Grade 60 Rebar {run_suffix}",
                    "quantity": 100.0,
                    "unit_price": 500.0,
                    "tax_rate": 0.0
                }
            ]
        }
    )
    assert status in [200, 201], f"Failed to create AP invoice: {inv_data}"
    invoice_id = inv_data["id"]
    assert float(inv_data["total_amount"]) == 50000.0
    print(f"   ✓ Registered AP Invoice: {inv_number} ($50,000.00, Status: {inv_data['status']})")

    # -------------------------------------------------------------------------
    # STEP 12: Execute 3-Way Match Verification
    # -------------------------------------------------------------------------
    print("12. Executing 3-Way Match Engine (PO vs GRN vs Invoice)...")
    status, match_report = make_request(
        f"{API_BASE}/ap/invoices/{invoice_id}/match",
        method="POST",
        headers=headers
    )
    assert status == 200, f"Match check failed: {match_report}"
    assert match_report["is_matched"] is True, f"Invoice was not matched: {match_report}"
    assert match_report["matching_status"] == "MATCHED"
    assert float(match_report["variance_amount"]) == 0.0
    print(f"   ✓ 3-Way Match Verified: Invoice {match_report['invoice_number']} matches PO {match_report['po_number']} & GRN {match_report['grn_number']} with Zero Variance.")

    # -------------------------------------------------------------------------
    # STEP 13: Approve and Post AP Invoice to General Ledger
    # -------------------------------------------------------------------------
    print("13. Approving and Posting AP Invoice to General Ledger (GL)...")
    status, appr_inv = make_request(
        f"{API_BASE}/ap/invoices/{invoice_id}/approve",
        method="POST",
        headers=headers
    )
    assert status == 200 and appr_inv["status"] == "APPROVED"

    status, posted_inv = make_request(
        f"{API_BASE}/ap/invoices/{invoice_id}/post",
        method="POST",
        headers=headers
    )
    assert status == 200, f"Failed to post invoice: {posted_inv}"
    assert posted_inv["status"] == "POSTED"
    journal_id = posted_inv["journal_id"]
    assert journal_id is not None, "Invoice posted without creating a journal entry"
    print(f"   ✓ Posted Invoice {inv_number} to GL: Generated Journal {journal_id}")

    # -------------------------------------------------------------------------
    # STEP 14: Verify GL Balanced Journal Voucher & Double-Entry Integrity
    # -------------------------------------------------------------------------
    print("14. Verifying Double-Entry General Ledger Integrity...")
    status, j_data = make_request(
        f"{API_BASE}/accounting/journals/{journal_id}",
        headers=headers
    )
    assert status == 200, f"Failed to load journal: {j_data}"
    assert j_data["status"] == "POSTED"
    assert float(j_data["total_debit"]) == 50000.0
    assert float(j_data["total_credit"]) == 50000.0
    print(f"   ✓ Balanced Journal Voucher verified: Total Debits (${float(j_data['total_debit']):,.2f}) == Total Credits (${float(j_data['total_credit']):,.2f})")

    # Verify Trial Balance
    status, tb = make_request(f"{API_BASE}/reports/accounting/trial-balance", headers=headers)
    assert status == 200
    assert float(tb["total_debit"]) == float(tb["total_credit"])
    print(f"   ✓ Chart of Accounts Trial Balance: ${float(tb['total_debit']):,.2f} Debits == ${float(tb['total_credit']):,.2f} Credits (100% Balanced).")

    # -------------------------------------------------------------------------
    # STEP 15: Verify Project & Executive Management Reporting
    # -------------------------------------------------------------------------
    print("15. Verifying Management Reporting & Executive KPIs...")
    status, rep_proj = make_request(
        f"{API_BASE}/reports/projects/{project_id}/dashboard",
        headers=headers
    )
    assert status == 200
    assert float(rep_proj["actual_cost"]) == 20000.0
    assert float(rep_proj["committed_cost"]) == 50000.0

    status, exec_rep = make_request(f"{API_BASE}/reports/executive-dashboard", headers=headers)
    assert status == 200
    assert exec_rep["is_ledger_balanced"] is True
    print(f"   ✓ Executive Reporting confirms: Project Actual Cost=${float(rep_proj['actual_cost']):,.2f}, Committed=${float(rep_proj['committed_cost']):,.2f}, Ledger Balanced=True.")

    # -------------------------------------------------------------------------
    # STEP 16: Independent Direct PostgreSQL Database Check
    # -------------------------------------------------------------------------
    print("\n16. Running Independent Database Verification directly against PostgreSQL...")
    conn = get_db_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check purchase_orders
        cur.execute("SELECT id, po_number, status, total_amount FROM purchase_orders WHERE id = %s;", (po_id,))
        db_po = cur.fetchone()
        assert db_po is not None and db_po["po_number"] == po_number
        assert Decimal(str(db_po["total_amount"])) == Decimal("50000.00")
        print(f"   ✓ [DB] purchase_orders: {db_po['po_number']} | Status={db_po['status']} | Total=${db_po['total_amount']}")

        # Check goods_receipts
        cur.execute("SELECT id, receipt_number, status FROM goods_receipts WHERE id = %s;", (grn_id,))
        db_grn = cur.fetchone()
        assert db_grn is not None and db_grn["receipt_number"] == grn_number
        assert db_grn["status"] == "POSTED"
        print(f"   ✓ [DB] goods_receipts: {db_grn['receipt_number']} | Status={db_grn['status']}")

        # Check inventory_transactions
        cur.execute(
            "SELECT id, transaction_type, quantity, unit_cost FROM inventory_transactions WHERE reference_id IN (%s, %s);",
            (grn_id, issue_id)
        )
        db_txns = cur.fetchall()
        assert len(db_txns) >= 2, f"Expected at least 2 inventory transactions, found {len(db_txns)}"
        types = [t["transaction_type"] for t in db_txns]
        assert "RECEIPT" in types and "ISSUE" in types
        print(f"   ✓ [DB] inventory_transactions: {len(db_txns)} records ({', '.join(types)}) verified in audit ledger")

        # Check material_issues
        cur.execute("SELECT id, issue_number, status, project_id FROM material_issues WHERE id = %s;", (issue_id,))
        db_iss = cur.fetchone()
        assert db_iss is not None and db_iss["issue_number"] == iss_number
        assert db_iss["status"] == "POSTED"
        assert str(db_iss["project_id"]) == str(project_id)
        print(f"   ✓ [DB] material_issues: {db_iss['issue_number']} | Status={db_iss['status']} | Project={db_iss['project_id']}")

        # Check ap_invoices
        cur.execute("SELECT id, number, status, matching_status, total_amount, journal_id FROM ap_invoices WHERE id = %s;", (invoice_id,))
        db_inv = cur.fetchone()
        assert db_inv is not None and db_inv["number"] == inv_number
        assert db_inv["status"] == "POSTED"
        assert db_inv["matching_status"] == "MATCHED"
        assert str(db_inv["journal_id"]) == str(journal_id)
        print(f"   ✓ [DB] ap_invoices: {db_inv['number']} | Status={db_inv['status']} | Matched={db_inv['matching_status']} | Journal={db_inv['journal_id']}")

        # Check journals
        cur.execute("SELECT id, reference, status, description FROM journals WHERE id = %s;", (journal_id,))
        db_j = cur.fetchone()
        assert db_j is not None and db_j["status"] == "POSTED"
        print(f"   ✓ [DB] journals: Ref={db_j['reference']} | Status={db_j['status']} | Desc={db_j['description']}")

        # Check journal_lines
        cur.execute("SELECT account_id, debit, credit FROM journal_lines WHERE journal_id = %s;", (journal_id,))
        db_lines = cur.fetchall()
        assert len(db_lines) >= 2
        sum_debit = sum(Decimal(str(l["debit"])) for l in db_lines)
        sum_credit = sum(Decimal(str(l["credit"])) for l in db_lines)
        assert sum_debit == sum_credit == Decimal("50000.00")
        print(f"   ✓ [DB] journal_lines: {len(db_lines)} lines strictly balanced (Debits ${sum_debit} == Credits ${sum_credit})")

        # Check project cost source records
        cur.execute(
            """
            SELECT mi.issue_number, mil.quantity, mil.unit_cost, (mil.quantity * mil.unit_cost) AS total_actual_cost
            FROM material_issues mi
            JOIN material_issue_lines mil ON mi.id = mil.material_issue_id
            WHERE mi.project_id = %s AND mi.status = 'POSTED';
            """,
            (project_id,)
        )
        db_costs = cur.fetchall()
        assert len(db_costs) >= 1
        total_mat_cost = sum(Decimal(str(c["total_actual_cost"])) for c in db_costs)
        assert total_mat_cost == Decimal("20000.00")
        print(f"   ✓ [DB] project cost source records: {len(db_costs)} material issue line(s) yielding ${total_mat_cost:,.2f} actual site cost")
    conn.close()
    print("   ✓ Independent database verification succeeded with 100% data integrity.")

    # -------------------------------------------------------------------------
    # STEP 17: Container Restart Persistence Verification
    # -------------------------------------------------------------------------
    print("\n17. Testing Container Restart Persistence (Stopping and Restarting API Service)...")
    ret, out, err = run_cmd(["docker", "restart", "modern_construction_erp-api-1"])
    assert ret == 0, f"Failed to restart container: {err}"
    print("   ✓ Container restarted. Waiting for FastAPI service readiness...")

    # Wait for API to become healthy
    ready = False
    for _ in range(30):
        time.sleep(1)
        try:
            req = urllib.request.Request("http://localhost:8000/health/ready")
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok":
                    ready = True
                    break
        except Exception:
            pass
    assert ready, "API service did not become ready after container restart!"
    print("   ✓ API service is back online and healthy.")

    # Re-login after restart
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{API_BASE}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
    ) as resp:
        token_after = json.loads(resp.read().decode("utf-8")).get("access_token")
    headers_after = {
        "Authorization": f"Bearer {token_after}",
        "Content-Type": "application/json"
    }

    # Verify project cost after restart
    status, cost_after_restart = make_request(
        f"{API_BASE}/project-cost/projects/{project_id}/costs/kpi",
        headers=headers_after
    )
    assert status == 200
    assert float(cost_after_restart["total_actual"]) == 20000.0
    print(f"   ✓ [After Restart] Project Actual Cost preserved: ${float(cost_after_restart['total_actual']):,.2f}")

    # Verify AP Invoice status after restart
    status, inv_after_restart = make_request(
        f"{API_BASE}/ap/invoices/{invoice_id}",
        headers=headers_after
    )
    assert status == 200
    assert inv_after_restart["status"] == "POSTED"
    assert str(inv_after_restart["journal_id"]) == str(journal_id)
    print(f"   ✓ [After Restart] AP Invoice preserved: Status={inv_after_restart['status']}, Journal={inv_after_restart['journal_id']}")

    # Verify Inventory balance after restart
    status, bal_after_restart = make_request(f"{API_BASE}/inventory/balances", headers=headers_after)
    assert status == 200
    b_found = next(
        (b for b in bal_after_restart if b["warehouse_id"] == warehouse_id and b["material_id"] == material_id),
        None
    )
    assert b_found is not None and float(b_found["quantity"]) == 60.0
    print(f"   ✓ [After Restart] Inventory stock preserved: {b_found['quantity']} TON")

    # -------------------------------------------------------------------------
    # STEP 18: Security & Negative Tenant Isolation Test
    # -------------------------------------------------------------------------
    print("\n18. Testing Pre-Mutation Cross-Tenant Security & Isolation Enforcement...")
    # Create Tenant B and User B directly in database
    conn = get_db_connection()
    tenant_b_id = str(uuid.uuid4())
    user_b_id = str(uuid.uuid4())
    user_b_email = f"attacker_{run_suffix}@tenantb.com"
    with conn.cursor() as cur:
        # Insert Tenant B if not exists
        cur.execute(
            "INSERT INTO tenants (id, name, created_at, updated_at) VALUES (%s, %s, NOW(), NOW()) ON CONFLICT (id) DO NOTHING;",
            (tenant_b_id, f"Foreign Tenant B {run_suffix}")
        )
        # Hash password with bcrypt
        import bcrypt
        salt = bcrypt.gensalt()
        h_pw = bcrypt.hashpw("Password123!".encode("utf-8"), salt).decode("utf-8")

        cur.execute(
            """
            INSERT INTO users (id, email, hashed_password, first_name, last_name, is_active, is_superuser, tenant_id, created_at, updated_at)
            VALUES (%s, %s, %s, 'Tenant', 'User', true, false, %s, NOW(), NOW());
            """,
            (user_b_id, user_b_email, h_pw, tenant_b_id)
        )
        conn.commit()
    conn.close()

    # Login as User B
    login_b_data = urllib.parse.urlencode({
        "username": user_b_email,
        "password": "Password123!"
    }).encode("utf-8")
    with urllib.request.urlopen(
        urllib.request.Request(
            f"{API_BASE}/auth/login",
            data=login_b_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
    ) as resp:
        token_b = json.loads(resp.read().decode("utf-8")).get("access_token")
    headers_b = {
        "Authorization": f"Bearer {token_b}",
        "Content-Type": "application/json"
    }

    # Attempt 1: Tenant B tries to read Tenant A's project
    status_cross_p, res_cross_p = make_request(
        f"{API_BASE}/projects/{project_id}",
        headers=headers_b
    )
    assert status_cross_p in [403, 404], f"Expected 403 or 404 for cross-tenant project read, got {status_cross_p}"
    print(f"   ✓ Cross-tenant read rejected: Tenant B cannot read Tenant A's project (HTTP {status_cross_p})")

    # Attempt 2: Tenant B tries to issue materials against Tenant A's warehouse and project
    status_cross_m, res_cross_m = make_request(
        f"{API_BASE}/inventory/material-issues",
        method="POST",
        headers=headers_b,
        data={
            "issue_number": f"ISS-ATTACK-{run_suffix}",
            "warehouse_id": warehouse_id,
            "project_id": project_id,
            "cost_code_id": cost_code_id,
            "date": "2026-09-08",
            "purpose": "Malicious Cross-Tenant Issue",
            "lines": [
                {
                    "material_id": material_id,
                    "quantity": 10.0,
                    "notes": "Unauthorized depletion"
                }
            ]
        }
    )
    assert status_cross_m in [403, 404], f"Expected 403/404 for cross-tenant material issue, got {status_cross_m}"
    print(f"   ✓ Cross-tenant mutation rejected: Tenant B cannot issue Tenant A's inventory (HTTP {status_cross_m})")

    # Attempt 3: Tenant B tries to invoice Tenant A's PO
    status_cross_inv, res_cross_inv = make_request(
        f"{API_BASE}/ap/invoices",
        method="POST",
        headers=headers_b,
        data={
            "number": f"INV-ATTACK-{run_suffix}",
            "supplier_id": supplier_id,
            "purchase_order_id": po_id,
            "date": "2026-09-08",
            "due_date": "2026-10-08",
            "lines": [
                {
                    "purchase_order_line_id": po_line_id,
                    "material_id": material_id,
                    "description": "Unauthorized cross-tenant line",
                    "quantity": 10.0,
                    "unit_price": 500.0
                }
            ]
        }
    )
    assert status_cross_inv in [400, 403, 404, 422], f"Expected rejection for cross-tenant invoice, got {status_cross_inv}"
    print(f"   ✓ Cross-tenant mutation rejected: Tenant B cannot invoice Tenant A's PO (HTTP {status_cross_inv})")

    # Verify no malicious records were written to DB
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM material_issues WHERE issue_number = %s;", (f"ISS-ATTACK-{run_suffix}",))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT count(*) FROM ap_invoices WHERE number = %s;", (f"INV-ATTACK-{run_suffix}",))
        assert cur.fetchone()[0] == 0
    conn.close()
    print("   ✓ DB confirmation: 0 malicious records written to database. Application pre-mutation validation enforced.")

    print("\n======================================================================")
    print("🎉 STAGE 34 AUTHORITATIVE USER JOURNEY & WORKFLOW HARDENING COMPLETE!")
    print("======================================================================")


if __name__ == "__main__":
    main()
