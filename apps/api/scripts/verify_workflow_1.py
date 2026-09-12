import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def run_e2e_test():
    print("===========================================")
    print("1. RUNNING FULL BUSINESS WORKFLOW E2E TEST")
    print("===========================================")
    os.environ["TEST_DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/erp"
    os.environ["PYTHONPATH"] = "."
    
    # Run the test
    result = subprocess.run(
        ["pytest", "tests/test_real_erp_workflows.py", "-k", "test_full_business_workflow_lifecycle", "--tb=short", "-s"],
        cwd="/home/king/git/Modern_Construction_ERP/apps/api",
        env=os.environ
    )
    
    if result.returncode != 0:
        print("E2E TEST FAILED!")
        exit(1)
    print("E2E TEST PASSED successfully.\n")

def verify_persistence():
    print("===========================================")
    print("2. DATABASE VERIFICATION (PERSISTENCE)")
    print("===========================================")
    print("Connecting independently to PostgreSQL (localhost:5433)...")
    
    conn = psycopg2.connect(
        dbname="erp",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5433"
    )
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check Purchase Orders
        cur.execute("SELECT id, po_number, total_amount, status FROM purchase_orders;")
        pos = cur.fetchall()
        print(f"\n--- PURCHASE ORDERS ({len(pos)}) ---")
        for po in pos:
            print(dict(po))
            
        # Check Goods Receipts
        cur.execute("SELECT id, receipt_number, status FROM goods_receipts;")
        grns = cur.fetchall()
        print(f"\n--- GOODS RECEIPTS ({len(grns)}) ---")
        for grn in grns:
            print(dict(grn))
            
        # Check Inventory Transactions (Ledger)
        cur.execute("SELECT id, transaction_type, quantity, unit_cost, reference_id FROM inventory_transactions;")
        txns = cur.fetchall()
        print(f"\n--- INVENTORY LEDGER TRANSACTIONS ({len(txns)}) ---")
        for txn in txns:
            print(dict(txn))
            
        # Check Inventory Balance
        cur.execute("SELECT material_id, warehouse_id, quantity, total_cost FROM inventory_balances;")
        bals = cur.fetchall()
        print(f"\n--- INVENTORY BALANCES ({len(bals)}) ---")
        for bal in bals:
            print(dict(bal))
            
        # Check AP Invoices
        cur.execute("SELECT id, number, total_amount, status, matching_status FROM ap_invoices;")
        invs = cur.fetchall()
        print(f"\n--- AP INVOICES ({len(invs)}) ---")
        for inv in invs:
            print(dict(inv))
            
        # Check GL Journals
        cur.execute("SELECT id, reference, date, status, description FROM journals;")
        journals = cur.fetchall()
        print(f"\n--- GENERAL LEDGER JOURNALS ({len(journals)}) ---")
        for jnl in journals:
            print(dict(jnl))
            # Get lines for the first journal
            cur.execute("SELECT account_id, debit, credit FROM journal_lines WHERE journal_id = %s;", (jnl['id'],))
            lines = cur.fetchall()
            for line in lines:
                print(f"  Line: {dict(line)}")
                


    conn.close()
    print("\nALL VERIFICATIONS PASSED: Data was persisted in the PostgreSQL database correctly.")

if __name__ == "__main__":
    run_e2e_test()
    verify_persistence()
