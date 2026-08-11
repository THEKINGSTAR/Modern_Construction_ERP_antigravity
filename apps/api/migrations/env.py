import logging
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.config import settings
from app.core.database import Base
from app.models.tenant import Tenant
from app.models.legal_entity import LegalEntity
from app.models.branch import Branch
from app.models.user import User
from app.models.auth import Role, Permission, UserRole, RolePermission
from app.models.org_settings import Currency, ExchangeRate, FiscalYear, AccountingPeriod, TenantSettings
from app.models.clients import Client, ClientContact
from app.models.projects import Project
from app.models.contracts import Contract, ContractType
from app.models.wbs import WBSNode
from app.models.cost_codes import CostCode
from app.models.boq import BOQ, BOQRevision, BOQItem
from app.models.estimates import Estimate, EstimateRevision, EstimateItem
from app.models.budgets import Budget, BudgetLine
from app.models.suppliers import Supplier, SupplierContact
from app.models.requisitions import PurchaseRequisition, PurchaseRequisitionLine
from app.models.rfqs import RFQ, RFQLine
from app.models.quotations import SupplierQuotation, SupplierQuotationLine
from app.models.purchase_orders import PurchaseOrder, PurchaseOrderLine
from app.models.materials import Material
from app.models.warehouses import Warehouse
from app.models.inventory import InventoryTransaction, InventoryBalance
from app.models.goods_receipts import GoodsReceipt, GoodsReceiptLine
from app.models.material_issues import MaterialIssue, MaterialIssueLine
from app.models.inventory_transfers import InventoryTransfer, InventoryTransferLine
from app.models.inventory_adjustments import InventoryAdjustment, InventoryAdjustmentLine

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
