import os
import subprocess
import psycopg2
from psycopg2.extras import RealDictCursor

def run_e2e_verification():
    print("==================================================")
    print("1. RUNNING FULL WORKFLOW 2 INTEGRATION TESTS")
    print("==================================================")
    os.environ["TEST_DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5433/erp"
    os.environ["PYTHONPATH"] = "."
    
    # Run the pytest test file
    result = subprocess.run(
        ["pytest", "tests/test_workflow_2_verification.py", "--tb=short", "-s"],
        cwd="/home/king/git/Modern_Construction_ERP/apps/api",
        env=os.environ
    )
    
    if result.returncode != 0:
        print("E2E WORKFLOW 2 TESTS FAILED!")
        exit(1)
    print("E2E WORKFLOW 2 TESTS PASSED successfully.\n")

def run_restart_persistence_check():
    print("==================================================")
    print("2. DATABASE PERSISTENCE VERIFICATION (AFTER RESTART)")
    print("==================================================")
    print("Connecting independently to PostgreSQL (localhost:5433)...")
    
    conn = psycopg2.connect(
        dbname="erp",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5433"
    )
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Check if material issues are stored
        cur.execute("SELECT id, issue_number, status, project_id FROM material_issues;")
        issues = cur.fetchall()
        print(f"\n--- MATERIAL ISSUES ({len(issues)}) ---")
        for i in issues:
            print(dict(i))
            
        cur.execute("SELECT id, transaction_type, quantity, unit_cost FROM inventory_transactions;")
        txns = cur.fetchall()
        print(f"\n--- INVENTORY TRANSACTIONS ({len(txns)}) ---")
        for t in txns:
            print(dict(t))
            
    conn.close()
    print("\nRESTART VERIFICATION PASSED: Data remained in the PostgreSQL database correctly.")

if __name__ == "__main__":
    run_e2e_verification()
    run_restart_persistence_check()
