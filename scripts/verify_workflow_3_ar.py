#!/usr/bin/env bash
#!/usr/bin/env python3
"""
scripts/verify_workflow_3_ar.py — Commercial Progress Billing & AR Settlement Verification.
Validates complete cross-domain workflow:
  Client -> Contract -> IPC Payment Application -> AR Invoice -> GL Posting (with Retainage) -> Cash Receipt & Settlement.
"""

import sys
import os
import uuid
import json
import urllib.request
import urllib.error
from decimal import Decimal
from datetime import date
import psycopg2

BASE_URL = "http://localhost:8000/api/v1"
DB_HOST = "localhost"
DB_PORT = 5434
DB_NAME = "erp"
DB_USER = "postgres"
DB_PASS = "postgres"

def log_step(step_num: int, title: str):
    print(f"\n[{step_num}/10] {title}...")

def make_req(url: str, method: str = "GET", data: dict = None, headers: dict = None):
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
            parsed = {"raw": err_body}
        return e.code, parsed

def assert_res(status: int, data: dict, expected_status: int, context: str):
    if status != expected_status:
        print(f"FAILED {context}: Status {status}, Response: {data}", file=sys.stderr)
        sys.exit(1)
    return data

def main():
    print("======================================================================")
    print("WORKFLOW 3: COMMERCIAL PROGRESS BILLING & AR CASH SETTLEMENT")
    print("======================================================================")
    run_id = uuid.uuid4().hex[:6].upper()

    # 1. Authenticate ERP User
    log_step(1, "Authenticating Admin User")
    import urllib.parse
    login_body = urllib.parse.urlencode({
        "username": "demo@apexconstruction.com",
        "password": "DemoPassword2026!"
    }).encode("utf-8")
    login_req = urllib.request.Request(
        f"{BASE_URL}/auth/login",
        data=login_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST"
    )
    with urllib.request.urlopen(login_req) as resp:
        login_data = json.loads(resp.read().decode("utf-8"))
    token = login_data["access_token"]
    user_tenant_id = login_data.get("tenant_id")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    if user_tenant_id:
        headers["X-Tenant-ID"] = user_tenant_id
    print("   ✓ Authenticated successfully.")

    # 2. Setup Client and Project
    log_step(2, "Setting up Client and Active Construction Project")
    s, d = make_req(
        f"{BASE_URL}/clients/",
        method="POST",
        headers=headers,
        data={
            "name": f"Metropolitan Port Authority {run_id}",
            "contact_email": f"director_{run_id}@portauthority.org",
            "status": "ACTIVE"
        }
    )
    client_data = assert_res(s, d, 201, "Create Client")
    client_id = client_data["id"]

    s, d = make_req(
        f"{BASE_URL}/projects/",
        method="POST",
        headers=headers,
        data={
            "project_number": f"PRJ-WF3-{run_id}",
            "name": f"Harbor Terminal Expansion {run_id}",
            "status": "ACTIVE",
            "client_id": client_id
        }
    )
    proj_data = assert_res(s, d, 201, "Create Project")
    project_id = proj_data["id"]
    print(f"   ✓ Client: {client_data['name']} | Project: {proj_data['name']}")

    # 3. Create Contract Type & Prime Construction Contract
    log_step(3, "Creating Prime Commercial Contract with Retainage")
    s, types = make_req(f"{BASE_URL}/contracts/types", method="GET", headers=headers)
    if s == 200 and types:
        ct_id = types[0]["id"]
    else:
        s, d = make_req(
            f"{BASE_URL}/contracts/types",
            method="POST",
            headers=headers,
            data={"name": "Lump Sum Turnkey (WF3)", "description": "Lump sum with standard 10% retainage"}
        )
        ct_id = assert_res(s, d, 201, "Create Contract Type")["id"]

    s, d = make_req(
        f"{BASE_URL}/contracts",
        method="POST",
        headers=headers,
        data={
            "project_id": project_id,
            "client_id": client_id,
            "contract_number": f"CTR-WF3-{run_id}",
            "contract_type_id": ct_id,
            "original_value": 1000000.0,
            "currency_code": "USD",
            "retention_rate": 0.10,
            "status": "ACTIVE"
        }
    )
    contract_data = assert_res(s, d, 201, "Create Contract")
    contract_id = contract_data["id"]
    print(f"   ✓ Created Contract: {contract_data['contract_number']} (Value: $1,000,000.00, Retention: 10%)")

    # 4. Resolve Accounting Period
    log_step(4, "Resolving Active Accounting Period")
    s, periods = make_req(f"{BASE_URL}/settings/accounting-periods", method="GET", headers=headers)
    if s != 200 or not periods:
        print("FAILED: No accounting periods configured.", file=sys.stderr)
        sys.exit(1)
    period_id = periods[0]["id"]
    period_date = periods[0].get("start_date", "2026-09-15")
    print(f"   ✓ Accounting Period: {periods[0]['name']} (Valid Date: {period_date})")

    # 5. Create and Approve Client Payment Application (IPC)
    log_step(5, "Submitting and Approving Client Payment Application (IPC)")
    # IPC: Gross work = $100,000.00, Retention = $10,000.00, Net Due = $90,000.00
    ipc_payload = {
        "contract_id": contract_id,
        "accounting_period_id": period_id,
        "number": f"IPC-{run_id}-01",
        "date": period_date,
        "gross_work": "100000.00",
        "previous_certified_work": "0.00",
        "retention_amount": "10000.00",
        "advance_recovery_amount": "0.00",
        "deductions_amount": "0.00",
        "adjustments_amount": "0.00"
    }
    s, d = make_req(f"{BASE_URL}/commercial/client-payment-applications", method="POST", headers=headers, data=ipc_payload)
    ipc_data = assert_res(s, d, 201, "Create Client Payment Application")
    ipc_id = ipc_data["id"]

    # Approve IPC
    s, d = make_req(f"{BASE_URL}/commercial/client-payment-applications/{ipc_id}/approve", method="POST", headers=headers)
    assert_res(s, d, 200, "Approve IPC")
    print(f"   ✓ IPC {ipc_payload['number']} Approved: Gross=$100,000.00, Retention=$10,000.00, Net Due=$90,000.00")

    # 6. Generate AR Invoice from Payment Application
    log_step(6, "Generating AR Progress Billing Invoice from Approved IPC")
    s, d = make_req(f"{BASE_URL}/ar/invoices/from-payment-application/{ipc_id}", method="POST", headers=headers)
    inv_data = assert_res(s, d, 201, "Generate AR Invoice from IPC")
    invoice_id = inv_data["id"]
    print(f"   ✓ Generated AR Invoice: {inv_data['number']} | Total Due: ${inv_data['total_amount']} | Status: {inv_data['status']}")

    # 7. Post AR Invoice to General Ledger
    log_step(7, "Posting AR Invoice to General Ledger (Debiting AR & Retainage)")
    s, posted_inv = make_req(f"{BASE_URL}/ar/invoices/{invoice_id}/post", method="POST", headers=headers)
    assert_res(s, posted_inv, 200, "Post AR Invoice")
    journal_id = posted_inv.get("journal_id")
    print(f"   ✓ Posted to GL: Journal ID = {journal_id}")

    # Verify Journal Entry Balancing (Debits == Credits)
    s, journal_data = make_req(f"{BASE_URL}/accounting/journals/{journal_id}", method="GET", headers=headers)
    assert_res(s, journal_data, 200, "Get Posted Journal")
    total_debits = sum(Decimal(str(line["debit"])) for line in journal_data["lines"])
    total_credits = sum(Decimal(str(line["credit"])) for line in journal_data["lines"])
    assert total_debits == total_credits, f"Journal out of balance: {total_debits} != {total_credits}"
    print(f"   ✓ Journal Balance Verified: Debits (${total_debits}) == Credits (${total_credits})")

    # 8. Check Initial Outstanding Balance
    log_step(8, "Verifying Open Accounts Receivable Balance")
    s, bal_data = make_req(f"{BASE_URL}/ar/invoices/{invoice_id}/balance", method="GET", headers=headers)
    assert_res(s, bal_data, 200, "Get AR Invoice Balance")
    open_balance = Decimal(str(bal_data["outstanding_balance"]))
    assert open_balance == Decimal("90000.00"), f"Expected 90000.00 open balance, got {open_balance}"
    print(f"   ✓ Verified Open Balance: ${open_balance}")

    # 9. Register Customer Collection Receipt and Settle Invoice
    log_step(9, "Recording Customer Cash Receipt & Full Invoice Settlement")
    s, bank_accounts = make_req(f"{BASE_URL}/bank/accounts", method="GET", headers=headers)
    bank_id = bank_accounts[0]["id"] if s == 200 and bank_accounts else None

    receipt_payload = {
        "reference": f"REC-{run_id}-01",
        "payment_type": "AR_RECEIPT",
        "date": period_date,
        "amount": "90000.00",
        "currency": "USD",
        "client_id": client_id,
        "bank_account_id": bank_id,
        "allocations": [
            {
                "ar_invoice_id": invoice_id,
                "amount": "90000.00"
            }
        ]
    }
    s, receipt_data = make_req(f"{BASE_URL}/ar/receipts", method="POST", headers=headers, data=receipt_payload)
    assert_res(s, receipt_data, 201, "Create AR Receipt")
    print(f"   ✓ Recorded Cash Receipt: {receipt_data['reference']} for $90,000.00")

    # Re-verify Invoice Status & Outstanding Balance
    s, final_inv = make_req(f"{BASE_URL}/ar/invoices/{invoice_id}", method="GET", headers=headers)
    assert_res(s, final_inv, 200, "Get Final Invoice State")
    assert final_inv["status"] == "PAID", f"Expected PAID status, got {final_inv['status']}"

    s, final_bal = make_req(f"{BASE_URL}/ar/invoices/{invoice_id}/balance", method="GET", headers=headers)
    assert_res(s, final_bal, 200, "Get Final Balance")
    settled_balance = Decimal(str(final_bal["outstanding_balance"]))
    assert settled_balance == Decimal("0.00"), f"Expected 0.00 balance, got {settled_balance}"
    print(f"   ✓ Invoice Status: {final_inv['status']} | Outstanding Balance: ${settled_balance}")

    # 10. Independent PostgreSQL Database Verification
    log_step(10, "Direct Independent PostgreSQL Persistence Verification")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    cur = conn.cursor()

    cur.execute("SELECT status, total_amount FROM ar_invoices WHERE id = %s", (invoice_id,))
    db_inv = cur.fetchone()
    assert db_inv is not None and db_inv[0] == "PAID"
    print(f"   ✓ [DB] ar_invoices: status={db_inv[0]}, total_amount={db_inv[1]}")

    cur.execute("SELECT sum(amount) FROM payment_allocations WHERE ar_invoice_id = %s", (invoice_id,))
    db_allocated = cur.fetchone()[0]
    assert Decimal(str(db_allocated)) == Decimal("90000.0000")
    print(f"   ✓ [DB] payment_allocations: allocated={db_allocated}")

    cur.execute("""
        SELECT sum(debit), sum(credit) FROM journal_lines 
        WHERE journal_id IN (%s, %s)
    """, (journal_id, receipt_data["journal_id"]))
    db_debits, db_credits = cur.fetchone()
    assert Decimal(str(db_debits)) == Decimal(str(db_credits))
    print(f"   ✓ [DB] journal_lines: Debits (${db_debits}) == Credits (${db_credits}) strictly balanced")

    conn.close()

    print("\n======================================================================")
    print("🎉 WORKFLOW 3: COMMERCIAL AR BILLING & SETTLEMENT FULLY VERIFIED!")
    print("======================================================================")

if __name__ == "__main__":
    main()
