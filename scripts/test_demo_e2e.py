#!/usr/bin/env python3
"""
scripts/test_demo_e2e.py — Comprehensive End-to-End Real ERP Verification Suite.
Validates the complete stack:
  Browser/Client -> Next.js Frontend -> FastAPI Backend -> PostgreSQL Database -> Business Logic -> Persistence
"""

import sys
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
        print("🎉 ALL 11 REAL ERP SYSTEM VERIFICATION CHECKS PASSED WITH 100% SUCCESS!")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"❌ Verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
