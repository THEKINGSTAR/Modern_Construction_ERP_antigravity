#!/usr/bin/env python3
"""
scripts/seed.py — Deterministic Demo Data Seeder for Modern Construction ERP.
Creates reproducible, clearly tagged DEMO entities across all core ERP domains.
Safe to re-run (idempotent; deletes prior demo tenant data if present).
"""

import sys
import os
from pathlib import Path
from uuid import UUID
from datetime import date
from decimal import Decimal

# Add apps/api to pythonpath
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

# Ensure required environment defaults exist before loading settings
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/erp")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "demo_secret_key_for_development_and_seeding_only")
os.environ.setdefault("ENVIRONMENT", "development")

# Preload all models to register SQLAlchemy relationships
import app.models.tenant
import app.models.legal_entity
import app.models.branch
import app.models.user
import app.models.auth
import app.models.org_settings
import app.models.materials
import app.models.warehouses
import app.models.inventory
import app.models.goods_receipts
import app.models.material_issues
import app.models.inventory_transfers
import app.models.inventory_adjustments
import app.models.dimensions
import app.models.accounting
import app.models.bank
import app.models.ap_ar
import app.models.commercial
import app.models.contracts
import app.models.projects
import app.models.clients
import app.models.suppliers

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.core.context import set_current_tenant_id
from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.models.branch import Branch
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, RolePermission
from app.models.org_settings import Currency, TenantSettings
from app.models.clients import Client, ClientContact
from app.models.suppliers import Supplier
from app.models.projects import Project, ProjectStatus
from app.models.contracts import Contract, ContractType, ContractStatus
from app.models.cost_codes import CostCode
from app.models.materials import Material
from app.models.warehouses import Warehouse, WarehouseType
from app.models.inventory import InventoryTransaction, InventoryBalance, TransactionType
from app.models.accounting import (
    ChartOfAccounts, Account, AccountType, Journal, JournalLine, JournalStatus
)
from app.models.ap_ar import APInvoice, APInvoiceLine, InvoiceStatus, InvoiceType

# Deterministic Demo UUIDs
DEMO_TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
DEMO_LEGAL_ENTITY_ID = UUID("22222222-2222-4222-8222-222222222222")
DEMO_BRANCH_ID = UUID("33333333-3333-4333-8333-333333333333")
DEMO_USER_ID = UUID("44444444-4444-4444-8444-444444444444")
DEMO_CLIENT_ID = UUID("55555555-5555-4555-8555-555555555555")
DEMO_SUPPLIER_ID = UUID("66666666-6666-4666-8666-666666666666")
DEMO_COST_CODE_ID = UUID("77777777-7777-4777-8777-777777777777")
DEMO_PROJECT_ID = UUID("88888888-8888-4888-8888-888888888888")
DEMO_WAREHOUSE_ID = UUID("99999999-9999-4999-8999-999999999999")
DEMO_MATERIAL_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
DEMO_COA_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
DEMO_CONTRACT_TYPE_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
DEMO_CONTRACT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")

def seed():
    db_url = os.environ["DATABASE_URL"]
    print(f"🌱 Modern Construction ERP — Seeding Demo Dataset")
    print(f"   Database target: {db_url.split('@')[-1] if '@' in db_url else db_url}")

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Seed Base Currency first (Global)
        usd = session.query(Currency).filter(Currency.code == "USD").first()
        if not usd:
            usd = Currency(code="USD", name="US Dollar", symbol="$")
            session.add(usd)
            session.flush()

        set_current_tenant_id(str(DEMO_TENANT_ID))

        # 1. Clean existing demo data if re-running
        old_tenants = session.query(Tenant).filter(
            (Tenant.id == DEMO_TENANT_ID) | (Tenant.name.like("%Apex Construction%"))
        ).all()
        for ot in old_tenants:
            print(f"   Cleaning prior DEMO tenant: {ot.name} ({ot.id})...")
            # Delete dependent records
            session.query(User).filter(User.tenant_id == ot.id).delete(synchronize_session=False)
            session.delete(ot)
        session.query(User).filter(User.email == "demo@apexconstruction.com").delete(synchronize_session=False)
        session.commit()

        print("   [1/9] Creating Demo Tenant, Legal Entity, Branch & Admin User...")
        tenant = Tenant(
            id=DEMO_TENANT_ID,
            name="Apex Construction Systems (DEMO)"
        )
        session.add(tenant)
        session.flush()

        legal_entity = LegalEntity(
            id=DEMO_LEGAL_ENTITY_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Apex Contracting LLC (DEMO)",
            tax_id="TAX-99887766",
            registration_number="REG-DEMO-2026"
        )
        session.add(legal_entity)
        session.flush()

        branch = Branch(
            id=DEMO_BRANCH_ID,
            tenant_id=DEMO_TENANT_ID,
            legal_entity_id=DEMO_LEGAL_ENTITY_ID,
            name="Metropolis Headquarters (DEMO)",
            code="HQ-01",
            address="100 Skyline Blvd, Suite 500, Metropolis"
        )
        session.add(branch)

        tenant_settings = TenantSettings(
            tenant_id=DEMO_TENANT_ID,
            base_currency_code="USD",
            default_locale="en",
            default_timezone="UTC",
            default_date_format="YYYY-MM-DD",
            default_number_format="#,##0.00"
        )
        session.add(tenant_settings)
        session.flush()

        user = User(
            id=DEMO_USER_ID,
            tenant_id=DEMO_TENANT_ID,
            email="demo@apexconstruction.com",
            first_name="Demo",
            last_name="Administrator",
            hashed_password=get_password_hash("DemoPassword2026!"),
            is_active=True,
            is_superuser=True
        )
        session.add(user)
        session.flush()

        print("   [2/9] Creating Demo Client & Supplier...")
        client = Client(
            id=DEMO_CLIENT_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Metropolis Development Group (DEMO)",
            legal_name="Metropolis Real Estate Holdings LLC",
            contact_information="contact@metropolis-dev.demo | +1-555-0199",
            billing_address="100 Skyline Blvd, Suite 400, Metropolis",
            tax_identifier="US-948172635",
            status="ACTIVE"
        )
        session.add(client)

        client_contact = ClientContact(
            tenant_id=DEMO_TENANT_ID,
            client_id=DEMO_CLIENT_ID,
            first_name="Sarah",
            last_name="Jenkins",
            email="sarah.jenkins@metropolis-dev.demo",
            phone="+1-555-0199",
            role="Vice President of Development",
            is_primary=True
        )
        session.add(client_contact)

        supplier = Supplier(
            id=DEMO_SUPPLIER_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Vulcan Steel & Materials (DEMO)",
            legal_name="Vulcan Heavy Materials Supply Corp",
            tax_identifier="US-123456789",
            address="77 Industrial Parkway, Sector 3, Metropolis",
            status="ACTIVE"
        )
        session.add(supplier)
        session.flush()

        print("   [3/9] Creating Cost Codes & Construction Project...")
        cost_code = CostCode(
            id=DEMO_COST_CODE_ID,
            tenant_id=DEMO_TENANT_ID,
            code="03-3000",
            name="Cast-in-Place Structural Concrete"
        )
        session.add(cost_code)
        session.flush()

        project = Project(
            id=DEMO_PROJECT_ID,
            tenant_id=DEMO_TENANT_ID,
            legal_entity_id=DEMO_LEGAL_ENTITY_ID,
            client_id=DEMO_CLIENT_ID,
            project_number="PRJ-2026-001",
            name="Skyline Commercial Tower (DEMO)",
            description="42-story mixed-use commercial tower with deep basement foundation",
            project_type="Commercial High-Rise",
            location="Metropolis Financial Center",
            start_date=date(2026, 1, 15),
            planned_end_date=date(2027, 12, 31),
            status=ProjectStatus.ACTIVE,
            base_currency="USD"
        )
        session.add(project)
        session.flush()

        print("   [4/9] Creating Prime Construction Contract...")
        contract_type = ContractType(
            id=DEMO_CONTRACT_TYPE_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Lump Sum Fixed Price (DEMO)",
            description="Standard guaranteed maximum lump sum commercial contract",
            is_active=True
        )
        session.add(contract_type)
        session.flush()

        contract = Contract(
            id=DEMO_CONTRACT_ID,
            tenant_id=DEMO_TENANT_ID,
            project_id=DEMO_PROJECT_ID,
            client_id=DEMO_CLIENT_ID,
            contract_number="CTR-2026-001",
            contract_type_id=DEMO_CONTRACT_TYPE_ID,
            original_value=Decimal("7500000.00"),
            current_value=Decimal("7500000.00"),
            currency_code="USD",
            start_date=date(2026, 1, 15),
            end_date=date(2027, 12, 31),
            retention_rate=Decimal("10.00"),
            payment_terms="Net 30",
            status=ContractStatus.ACTIVE
        )
        session.add(contract)
        session.flush()

        print("   [5/9] Creating Warehouse & Material Master...")
        warehouse = Warehouse(
            id=DEMO_WAREHOUSE_ID,
            tenant_id=DEMO_TENANT_ID,
            code="WH-MAIN",
            name="Skyline Central Site Warehouse (DEMO)",
            location="Metropolis Site 4 North Gate",
            type=WarehouseType.PROJECT,
            project_id=DEMO_PROJECT_ID
        )
        session.add(warehouse)

        material = Material(
            id=DEMO_MATERIAL_ID,
            tenant_id=DEMO_TENANT_ID,
            material_code="MAT-REBAR-16",
            name="High-Tensile Steel Rebar 16mm (DEMO)",
            description="Grade 60 deformed reinforcing carbon steel bars",
            category="Structural Metals",
            base_unit="TON",
            active=True
        )
        session.add(material)
        session.flush()

        print("   [6/9] Recording Ledger-Based Inventory Transactions & Balance...")
        tx_receipt = InventoryTransaction(
            tenant_id=DEMO_TENANT_ID,
            warehouse_id=DEMO_WAREHOUSE_ID,
            material_id=DEMO_MATERIAL_ID,
            project_id=DEMO_PROJECT_ID,
            transaction_type=TransactionType.RECEIPT,
            quantity=Decimal("100.00"),
            unit_cost=Decimal("850.00"),
            total_cost=Decimal("85000.00"),
            reference_type="PO",
            reference_id=DEMO_SUPPLIER_ID,
            transaction_date=date(2026, 2, 1)
        )
        session.add(tx_receipt)

        tx_issue = InventoryTransaction(
            tenant_id=DEMO_TENANT_ID,
            warehouse_id=DEMO_WAREHOUSE_ID,
            material_id=DEMO_MATERIAL_ID,
            project_id=DEMO_PROJECT_ID,
            transaction_type=TransactionType.ISSUE,
            quantity=Decimal("35.00"),
            unit_cost=Decimal("850.00"),
            total_cost=Decimal("29750.00"),
            reference_type="PROJECT",
            reference_id=DEMO_PROJECT_ID,
            transaction_date=date(2026, 2, 10)
        )
        session.add(tx_issue)

        balance = InventoryBalance(
            tenant_id=DEMO_TENANT_ID,
            warehouse_id=DEMO_WAREHOUSE_ID,
            material_id=DEMO_MATERIAL_ID,
            quantity=Decimal("65.00"),
            total_cost=Decimal("55250.00")
        )
        session.add(balance)
        session.flush()

        print("   [7/9] Setting Up Chart of Accounts & General Ledger...")
        coa = ChartOfAccounts(
            id=DEMO_COA_ID,
            tenant_id=DEMO_TENANT_ID,
            name="Standard Construction COA (DEMO)",
            description="Standard Construction Enterprise Chart of Accounts"
        )
        session.add(coa)
        session.flush()

        acc_cash = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="1010",
            name="Cash & Operating Bank (DEMO)",
            account_type=AccountType.ASSET,
            is_control_account=True
        )
        acc_ar = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="1200",
            name="Accounts Receivable (DEMO)",
            account_type=AccountType.ASSET,
            is_control_account=True
        )
        acc_inv = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="1300",
            name="Materials Inventory Asset (DEMO)",
            account_type=AccountType.ASSET,
            is_control_account=True
        )
        acc_ap = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="2010",
            name="Accounts Payable - Trade (DEMO)",
            account_type=AccountType.LIABILITY,
            is_control_account=True
        )
        acc_rev = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="4010",
            name="Commercial Construction Revenue (DEMO)",
            account_type=AccountType.REVENUE,
            is_control_account=False
        )
        acc_exp = Account(
            tenant_id=DEMO_TENANT_ID,
            chart_of_accounts_id=DEMO_COA_ID,
            account_code="5010",
            name="Direct Construction Materials Expense (DEMO)",
            account_type=AccountType.EXPENSE,
            is_control_account=False
        )
        session.add_all([acc_cash, acc_ar, acc_inv, acc_ap, acc_rev, acc_exp])
        session.flush()

        print("   [8/9] Recording Balanced Journal Entry (Golden Rule Compliance)...")
        journal = Journal(
            tenant_id=DEMO_TENANT_ID,
            date=date(2026, 2, 10),
            reference="JRN-2026-001",
            description="Initial Milestone Revenue Recognition & Material Consumption",
            status=JournalStatus.POSTED
        )
        session.add(journal)
        session.flush()

        jlines = [
            JournalLine(
                tenant_id=DEMO_TENANT_ID,
                journal_id=journal.id,
                account_id=acc_ar.id,
                debit=Decimal("750000.00"),
                credit=Decimal("0.00"),
                project_id=DEMO_PROJECT_ID,
                cost_code_id=DEMO_COST_CODE_ID
            ),
            JournalLine(
                tenant_id=DEMO_TENANT_ID,
                journal_id=journal.id,
                account_id=acc_rev.id,
                debit=Decimal("0.00"),
                credit=Decimal("750000.00"),
                project_id=DEMO_PROJECT_ID,
                cost_code_id=DEMO_COST_CODE_ID
            ),
            JournalLine(
                tenant_id=DEMO_TENANT_ID,
                journal_id=journal.id,
                account_id=acc_exp.id,
                debit=Decimal("29750.00"),
                credit=Decimal("0.00"),
                project_id=DEMO_PROJECT_ID,
                cost_code_id=DEMO_COST_CODE_ID
            ),
            JournalLine(
                tenant_id=DEMO_TENANT_ID,
                journal_id=journal.id,
                account_id=acc_inv.id,
                debit=Decimal("0.00"),
                credit=Decimal("29750.00"),
                project_id=DEMO_PROJECT_ID,
                cost_code_id=DEMO_COST_CODE_ID
            ),
        ]
        session.add_all(jlines)
        session.flush()

        print("   [9/9] Creating Verified AP Invoice from Supplier...")
        ap_invoice = APInvoice(
            tenant_id=DEMO_TENANT_ID,
            number="AP-VULCAN-001",
            supplier_id=DEMO_SUPPLIER_ID,
            date=date(2026, 2, 1),
            due_date=date(2026, 3, 3),
            status=InvoiceStatus.POSTED,
            invoice_type=InvoiceType.STANDARD,
            total_amount=Decimal("85000.00"),
            currency="USD",
            description="Steel rebar shipment for foundation stage"
        )
        session.add(ap_invoice)
        session.flush()

        ap_line = APInvoiceLine(
            tenant_id=DEMO_TENANT_ID,
            invoice_id=ap_invoice.id,
            project_id=DEMO_PROJECT_ID,
            cost_code_id=DEMO_COST_CODE_ID,
            description="100 TON High-Tensile Rebar 16mm",
            quantity=Decimal("100.00"),
            unit_price=Decimal("850.00"),
            line_total=Decimal("85000.00")
        )
        session.add(ap_line)

        session.commit()

        print("\n" + "=" * 70)
        print("🎉 DEMO DATA SEEDED SUCCESSFULLY")
        print("=" * 70)
        print(f"Tenant:         {tenant.name} ({tenant.id})")
        print(f"Admin User:     {user.email} (Password: DemoPassword2026!)")
        print(f"Project:        {project.project_number} — {project.name}")
        print(f"Contract:       {contract.contract_number} (Value: ${contract.current_value:,.2f})")
        print(f"Material Stock: {balance.quantity} TON in {warehouse.name} (Valuation: ${balance.total_cost:,.2f})")
        print(f"General Ledger: Posted Journal JRN-2026-001 (Balanced Debits == Credits: $779,750.00)")
        print(f"AP Invoice:     {ap_invoice.number} (${ap_invoice.total_amount:,.2f})")
        print("=" * 70)

    except Exception as e:
        session.rollback()
        print(f"[ERROR] Seeding failed: {e}", file=sys.stderr)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed()
