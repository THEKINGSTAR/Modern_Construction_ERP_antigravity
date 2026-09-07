import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date, timedelta
from app.models.ap_ar import InvoiceStatus, PaymentStatus, InvoiceType, PaymentType
from app.models.accounting import AccountType, Account, ChartOfAccounts
from app.models.suppliers import Supplier
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine, POStatus
from app.models.goods_receipts import GoodsReceipt, GoodsReceiptLine, GoodsReceiptStatus
from app.models.warehouses import Warehouse
from app.models.materials import Material
from app.models.bank import BankAccount
from app.models.org_settings import FiscalYear, AccountingPeriod

@pytest.fixture
def ap_setup(db_session, test_user):
    tenant_id = test_user.tenant_id
    user_id = test_user.id

    # 1. Chart of Accounts & GL Accounts
    coa = ChartOfAccounts(tenant_id=tenant_id, name="AP Test COA")
    db_session.add(coa)
    db_session.flush()

    ap_acc = Account(tenant_id=tenant_id, name="Accounts Payable - Trade", account_type=AccountType.LIABILITY, chart_of_accounts_id=coa.id, account_code="2010")
    exp_acc = Account(tenant_id=tenant_id, name="Direct Materials Expense", account_type=AccountType.EXPENSE, chart_of_accounts_id=coa.id, account_code="5010")
    cash_acc = Account(tenant_id=tenant_id, name="Cash & Bank", account_type=AccountType.ASSET, chart_of_accounts_id=coa.id, account_code="1010")
    db_session.add_all([ap_acc, exp_acc, cash_acc])
    db_session.flush()

    # 2. Fiscal Year & Open Accounting Period
    fy = FiscalYear(tenant_id=tenant_id, name="FY2026", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
    db_session.add(fy)
    db_session.flush()

    period = AccountingPeriod(tenant_id=tenant_id, fiscal_year_id=fy.id, name="Period-2026-09", start_date=date(2026, 9, 1), end_date=date(2026, 9, 30), is_closed=False)
    db_session.add(period)

    # 3. Bank Account
    bank = BankAccount(tenant_id=tenant_id, name="Operating Treasury", account_number="ACCT-98765", bank_name="First National Bank", gl_account_id=cash_acc.id)
    db_session.add(bank)

    # 4. Supplier
    supplier = Supplier(tenant_id=tenant_id, name="Apex Rebar & Steel Mills")
    db_session.add(supplier)
    db_session.flush()

    # 5. Material & Warehouse
    material = Material(tenant_id=tenant_id, material_code="MAT-TEST-STEEL", name="Structural Steel", base_unit="TON")
    warehouse = Warehouse(tenant_id=tenant_id, code="WH-TEST-01", name="Main Logistics Yard")
    db_session.add_all([material, warehouse])
    db_session.flush()

    # 6. Purchase Order
    po = PurchaseOrder(
        tenant_id=tenant_id,
        po_number=f"PO-TEST-{uuid4().hex[:6]}",
        supplier_id=supplier.id,
        status=POStatus.ISSUED,
        total_amount=Decimal("50000.0000")
    )
    db_session.add(po)
    db_session.flush()

    po_line = PurchaseOrderLine(
        tenant_id=tenant_id,
        purchase_order_id=po.id,
        item_description="Structural Steel Grade 60",
        unit="TON",
        quantity=Decimal("50.0000"),
        unit_price=Decimal("1000.0000"),
        amount=Decimal("50000.0000")
    )
    db_session.add(po_line)
    db_session.flush()

    # 7. Goods Receipt Note (GRN)
    grn = GoodsReceipt(
        tenant_id=tenant_id,
        receipt_number=f"GRN-TEST-{uuid4().hex[:6]}",
        purchase_order_id=po.id,
        supplier_id=supplier.id,
        warehouse_id=warehouse.id,
        date=date(2026, 9, 5),
        status=GoodsReceiptStatus.POSTED
    )
    db_session.add(grn)
    db_session.flush()

    grn_line = GoodsReceiptLine(
        tenant_id=tenant_id,
        goods_receipt_id=grn.id,
        purchase_order_line_id=po_line.id,
        material_id=material.id,
        received_quantity=Decimal("50.0000"),
        accepted_quantity=Decimal("50.0000"),
        rejected_quantity=Decimal("0.0000"),
        unit_cost=Decimal("1000.0000")
    )
    db_session.add(grn_line)
    db_session.commit()

    return {
        "supplier": supplier,
        "po": po,
        "po_line": po_line,
        "grn": grn,
        "grn_line": grn_line,
        "bank": bank,
        "material": material
    }

def test_ap_three_way_matching_and_approval(client, auth_headers, ap_setup):
    po = ap_setup["po"]
    po_line = ap_setup["po_line"]
    grn = ap_setup["grn"]
    supplier = ap_setup["supplier"]

    # 1. Create AP Vendor Invoice matched to PO and GRN
    inv_data = {
        "number": f"INV-TEST-{uuid4().hex[:6]}",
        "supplier_id": str(supplier.id),
        "purchase_order_id": str(po.id),
        "goods_receipt_id": str(grn.id),
        "date": "2026-09-06",
        "due_date": "2026-09-25",
        "invoice_type": "STANDARD",
        "currency": "USD",
        "description": "Invoice for Structural Steel Batch 1",
        "tax_amount": 2500.0,
        "lines": [
            {
                "purchase_order_line_id": str(po_line.id),
                "description": "Structural Steel Grade 60",
                "quantity": 50.0,
                "unit_price": 1000.0,
                "tax_rate": 5.0,
                "tax_amount": 2500.0
            }
        ]
    }
    create_res = client.post("/api/v1/ap/invoices", json=inv_data, headers=auth_headers)
    assert create_res.status_code == 201
    inv = create_res.json()
    assert inv["number"] == inv_data["number"]
    assert float(inv["total_amount"]) == 52500.0
    assert inv["matching_status"] == "MATCHED"

    # 2. Run 3-way match verification endpoint
    match_res = client.post(f"/api/v1/ap/invoices/{inv['id']}/match", headers=auth_headers)
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["is_matched"] is True
    assert match_data["matching_status"] == "MATCHED"
    assert match_data["can_approve"] is True
    assert float(match_data["variance_amount"]) == 0.0
    assert len(match_data["lines"]) == 1
    assert match_data["lines"][0]["line_status"] == "MATCHED"

    # 3. Approve the matched invoice
    appr_res = client.post(f"/api/v1/ap/invoices/{inv['id']}/approve", headers=auth_headers)
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "APPROVED"

    # 4. Post to General Ledger
    post_res = client.post(f"/api/v1/ap/invoices/{inv['id']}/post", headers=auth_headers)
    assert post_res.status_code == 200
    posted_inv = post_res.json()
    assert posted_inv["status"] == "POSTED"
    assert posted_inv["journal_id"] is not None

def test_ap_variance_detection(client, auth_headers, ap_setup):
    po = ap_setup["po"]
    po_line = ap_setup["po_line"]
    grn = ap_setup["grn"]
    supplier = ap_setup["supplier"]

    # Create Invoice with Price Variance (billed $1100 instead of PO $1000)
    inv_data = {
        "number": f"INV-VAR-{uuid4().hex[:6]}",
        "supplier_id": str(supplier.id),
        "purchase_order_id": str(po.id),
        "goods_receipt_id": str(grn.id),
        "date": "2026-09-06",
        "due_date": "2026-09-25",
        "invoice_type": "STANDARD",
        "currency": "USD",
        "lines": [
            {
                "purchase_order_line_id": str(po_line.id),
                "description": "Structural Steel Grade 60",
                "quantity": 50.0,
                "unit_price": 1100.0  # $100 price variance per ton
            }
        ]
    }
    create_res = client.post("/api/v1/ap/invoices", json=inv_data, headers=auth_headers)
    assert create_res.status_code == 201
    inv = create_res.json()

    match_res = client.post(f"/api/v1/ap/invoices/{inv['id']}/match", headers=auth_headers)
    assert match_res.status_code == 200
    match_data = match_res.json()
    assert match_data["is_matched"] is False
    assert match_data["matching_status"] == "VARIANCE"
    assert match_data["lines"][0]["line_status"] == "PRICE_VARIANCE"
    assert float(match_data["lines"][0]["price_variance"]) == 100.0

def test_ap_payment_and_summary(client, auth_headers, ap_setup):
    po = ap_setup["po"]
    supplier = ap_setup["supplier"]
    bank = ap_setup["bank"]

    # 1. Create and post an invoice
    inv_data = {
        "number": f"INV-PAY-{uuid4().hex[:6]}",
        "supplier_id": str(supplier.id),
        "date": "2026-09-06",
        "due_date": "2026-09-20",
        "lines": [
            {
                "description": "Welding and fabrication work",
                "quantity": 10.0,
                "unit_price": 1000.0
            }
        ]
    }
    inv = client.post("/api/v1/ap/invoices", json=inv_data, headers=auth_headers).json()
    client.post(f"/api/v1/ap/invoices/{inv['id']}/post", headers=auth_headers)

    # 2. Check summary before payment
    sum_res = client.get("/api/v1/ap/summary", headers=auth_headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert float(summary["total_payables"]) >= 10000.0

    # 3. Disburse payment
    pay_data = {
        "reference": f"VCH-{uuid4().hex[:6]}",
        "payment_type": "AP_PAYMENT",
        "date": "2026-09-07",
        "amount": 10000.0,
        "supplier_id": str(supplier.id),
        "bank_account_id": str(bank.id),
        "allocations": [
            {
                "ap_invoice_id": inv["id"],
                "amount": 10000.0
            }
        ]
    }
    pay_res = client.post("/api/v1/ap/payments", json=pay_data, headers=auth_headers)
    assert pay_res.status_code == 201
    payment = pay_res.json()
    assert payment["status"] == "POSTED"
    assert payment["journal_id"] is not None

    # 4. Verify invoice is marked as PAID
    inv_check = client.get(f"/api/v1/ap/invoices/{inv['id']}", headers=auth_headers).json()
    assert inv_check["status"] == "PAID"
    assert float(inv_check["outstanding_amount"]) == 0.0

def test_ap_tenant_isolation(client, auth_headers, ap_setup, db_session):
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.core.security import get_password_hash, create_access_token

    # Create second tenant
    tenant_b = Tenant(name="Tenant B Construction")
    db_session.add(tenant_b)
    db_session.flush()

    user_b = User(
        tenant_id=tenant_b.id,
        email=f"user_b_{uuid4().hex[:6]}@test.com",
        hashed_password=get_password_hash("password123"),
        first_name="User",
        last_name="B"
    )
    db_session.add(user_b)
    db_session.commit()

    token_b = create_access_token(data={"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant B tries to read Tenant A's invoices
    res = client.get("/api/v1/ap/invoices", headers=headers_b)
    assert res.status_code == 200
    assert len(res.json()) == 0  # Tenant B sees zero invoices from Tenant A
