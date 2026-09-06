#!/usr/bin/env python3
"""
scripts/test_demo_e2e.py — End-to-End ERP Verification Test Suite.
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
    req = urllib.request.Request(f"{WEB_BASE}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200, f"Expected 200 from Next.js, got {resp.status}"
        body = resp.read().decode("utf-8")
        assert "html" in body, "Expected HTML in Next.js response"
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
    new_proj_payload = json.dumps({
        "project_number": "PRJ-E2E-TEST-001",
        "name": "E2E Automated Verification Pier (DEMO)",
        "budget_amount": "3500000.00",
        "status": "ACTIVE"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/projects/", data=new_proj_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created = json.loads(resp.read().decode("utf-8"))
        assert created["project_number"] == "PRJ-E2E-TEST-001"
        print(f"   ✓ Created new project: {created['name']} ({created['project_number']})")

    print("6. Testing Clients Domain (Read & Create)...")
    new_client_payload = json.dumps({
        "name": "E2E Verification Client Ltd (DEMO)",
        "legal_name": "E2E Verification Client Limited",
        "contact_information": "e2e@test.demo",
        "status": "ACTIVE"
    }).encode("utf-8")
    req = urllib.request.Request(f"{API_BASE}/clients/", data=new_client_payload, headers=headers, method="POST")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        created_client = json.loads(resp.read().decode("utf-8"))
        print(f"   ✓ Created new client: {created_client['name']}")

    print("7. Testing Inventory Ledger Balances...")
    req = urllib.request.Request(f"{API_BASE}/inventory/balances", headers=headers)
    with urllib.request.urlopen(req) as resp:
        balances = json.loads(resp.read().decode("utf-8"))
        assert len(balances) >= 1, "Expected at least 1 warehouse balance"
        b = balances[0]
        qty = Decimal(b["quantity"])
        val = Decimal(b["total_cost"])
        assert qty > 0, "Inventory quantity must be positive"
        assert val > 0, "Inventory valuation must be positive"
        print(f"   ✓ Inventory verified: {qty} units, total valuation ${val:,.2f}")

    print("8. Testing Project Cost & Reporting Dashboard...")
    # Seeded project ID
    proj_id = "88888888-8888-4888-8888-888888888888"
    req = urllib.request.Request(f"{API_BASE}/reports/projects/{proj_id}/dashboard", headers=headers)
    with urllib.request.urlopen(req) as resp:
        dash = json.loads(resp.read().decode("utf-8"))
        contract_val = Decimal(dash["contract_value"])
        payable = Decimal(dash["payable"])
        assert contract_val == Decimal("7500000.00"), f"Expected $7.5M contract value, got {contract_val}"
        assert payable == Decimal("85000.00"), f"Expected $85k payable, got {payable}"
        print(f"   ✓ Reporting dashboard computed live metrics: Contract=${contract_val:,.2f}, Payable=${payable:,.2f}")

    print("9. Testing General Ledger Trial Balance (Golden Rule: Debits == Credits)...")
    req = urllib.request.Request(f"{API_BASE}/reports/accounting/trial-balance", headers=headers)
    with urllib.request.urlopen(req) as resp:
        tb = json.loads(resp.read().decode("utf-8"))
        total_debit = Decimal(tb["total_debit"])
        total_credit = Decimal(tb["total_credit"])
        assert total_debit == total_credit, f"Golden Rule broken! Debit {total_debit} != Credit {total_credit}"
        print(f"   ✓ Trial Balance balanced: Total Debits (${total_debit:,.2f}) == Total Credits (${total_credit:,.2f})")

def main():
    print("=" * 70)
    print("🚀 MODERN CONSTRUCTION ERP — RUNNABLE DEMO VERIFICATION SUITE")
    print("=" * 70)
    try:
        test_web_frontend()
        test_api_health()
        token = test_auth()
        test_erp_workflows(token)
        print("=" * 70)
        print("🎉 ALL 9 END-TO-END DEMO VERIFICATION CHECKS PASSED SUCCESSFULLY!")
        print("=" * 70)
        return 0
    except Exception as e:
        print(f"❌ Verification failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
