"""inventory_and_materials

Revision ID: 7f1ceb213a0d
Revises: 0192234924d4
Create Date: 2026-08-12 00:16:42.656527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7f1ceb213a0d'
down_revision: Union[str, None] = '0192234924d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. materials
    op.create_table('materials',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('material_code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('base_unit', sa.String(length=50), nullable=False),
        sa.Column('alternate_units', sa.Text(), nullable=True),
        sa.Column('conversion', sa.Text(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_materials_material_code'), 'materials', ['material_code'], unique=False)
    op.create_index(op.f('ix_materials_name'), 'materials', ['name'], unique=False)
    op.create_index(op.f('ix_materials_category'), 'materials', ['category'], unique=False)
    op.create_index(op.f('ix_materials_tenant_id'), 'materials', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_materials_active'), 'materials', ['active'], unique=False)

    # 2. warehouses
    op.create_table('warehouses',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('CENTRAL', 'PROJECT', 'TRANSIT', 'VIRTUAL', name='warehousetype'), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('manager_id', sa.UUID(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_warehouses_code'), 'warehouses', ['code'], unique=False)
    op.create_index(op.f('ix_warehouses_manager_id'), 'warehouses', ['manager_id'], unique=False)
    op.create_index(op.f('ix_warehouses_name'), 'warehouses', ['name'], unique=False)
    op.create_index(op.f('ix_warehouses_project_id'), 'warehouses', ['project_id'], unique=False)
    op.create_index(op.f('ix_warehouses_tenant_id'), 'warehouses', ['tenant_id'], unique=False)

    # 3. inventory_transactions
    op.create_table('inventory_transactions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=True),
        sa.Column('transaction_type', sa.Enum('OPENING', 'RECEIPT', 'ISSUE', 'TRANSFER_OUT', 'TRANSFER_IN', 'RETURN', 'ADJUSTMENT_IN', 'ADJUSTMENT_OUT', name='transactiontype'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', sa.UUID(), nullable=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_transactions_material_id'), 'inventory_transactions', ['material_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_project_id'), 'inventory_transactions', ['project_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_reference_id'), 'inventory_transactions', ['reference_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_reference_type'), 'inventory_transactions', ['reference_type'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_tenant_id'), 'inventory_transactions', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_transaction_date'), 'inventory_transactions', ['transaction_date'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_transaction_type'), 'inventory_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_inventory_transactions_warehouse_id'), 'inventory_transactions', ['warehouse_id'], unique=False)

    # 4. inventory_balances
    op.create_table('inventory_balances',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('total_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_balances_material_id'), 'inventory_balances', ['material_id'], unique=False)
    op.create_index(op.f('ix_inventory_balances_tenant_id'), 'inventory_balances', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_balances_warehouse_id'), 'inventory_balances', ['warehouse_id'], unique=False)

    # 5. goods_receipts
    op.create_table('goods_receipts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('receipt_number', sa.String(length=100), nullable=False),
        sa.Column('purchase_order_id', sa.UUID(), nullable=False),
        sa.Column('supplier_id', sa.UUID(), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'POSTED', 'CANCELLED', name='goodsreceiptstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['purchase_order_id'], ['purchase_orders.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goods_receipts_date'), 'goods_receipts', ['date'], unique=False)
    op.create_index(op.f('ix_goods_receipts_purchase_order_id'), 'goods_receipts', ['purchase_order_id'], unique=False)
    op.create_index(op.f('ix_goods_receipts_receipt_number'), 'goods_receipts', ['receipt_number'], unique=False)
    op.create_index(op.f('ix_goods_receipts_status'), 'goods_receipts', ['status'], unique=False)
    op.create_index(op.f('ix_goods_receipts_supplier_id'), 'goods_receipts', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_goods_receipts_tenant_id'), 'goods_receipts', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goods_receipts_warehouse_id'), 'goods_receipts', ['warehouse_id'], unique=False)

    # 6. goods_receipt_lines
    op.create_table('goods_receipt_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('goods_receipt_id', sa.UUID(), nullable=False),
        sa.Column('purchase_order_line_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('received_quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('accepted_quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('rejected_quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['goods_receipt_id'], ['goods_receipts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['purchase_order_line_id'], ['purchase_order_lines.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goods_receipt_lines_goods_receipt_id'), 'goods_receipt_lines', ['goods_receipt_id'], unique=False)
    op.create_index(op.f('ix_goods_receipt_lines_material_id'), 'goods_receipt_lines', ['material_id'], unique=False)
    op.create_index(op.f('ix_goods_receipt_lines_purchase_order_line_id'), 'goods_receipt_lines', ['purchase_order_line_id'], unique=False)
    op.create_index(op.f('ix_goods_receipt_lines_tenant_id'), 'goods_receipt_lines', ['tenant_id'], unique=False)

    # 7. material_issues
    op.create_table('material_issues',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('issue_number', sa.String(length=100), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('project_id', sa.UUID(), nullable=False),
        sa.Column('cost_code_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('requested_by_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'POSTED', 'CANCELLED', name='materialissuestatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['cost_code_id'], ['cost_codes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['requested_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_issues_cost_code_id'), 'material_issues', ['cost_code_id'], unique=False)
    op.create_index(op.f('ix_material_issues_date'), 'material_issues', ['date'], unique=False)
    op.create_index(op.f('ix_material_issues_issue_number'), 'material_issues', ['issue_number'], unique=False)
    op.create_index(op.f('ix_material_issues_project_id'), 'material_issues', ['project_id'], unique=False)
    op.create_index(op.f('ix_material_issues_requested_by_id'), 'material_issues', ['requested_by_id'], unique=False)
    op.create_index(op.f('ix_material_issues_status'), 'material_issues', ['status'], unique=False)
    op.create_index(op.f('ix_material_issues_tenant_id'), 'material_issues', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_material_issues_warehouse_id'), 'material_issues', ['warehouse_id'], unique=False)

    # 8. material_issue_lines
    op.create_table('material_issue_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('material_issue_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['material_issue_id'], ['material_issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_material_issue_lines_material_id'), 'material_issue_lines', ['material_id'], unique=False)
    op.create_index(op.f('ix_material_issue_lines_material_issue_id'), 'material_issue_lines', ['material_issue_id'], unique=False)
    op.create_index(op.f('ix_material_issue_lines_tenant_id'), 'material_issue_lines', ['tenant_id'], unique=False)

    # 9. inventory_transfers
    op.create_table('inventory_transfers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('transfer_number', sa.String(length=100), nullable=False),
        sa.Column('source_warehouse_id', sa.UUID(), nullable=False),
        sa.Column('destination_warehouse_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'POSTED', 'CANCELLED', name='inventorytransferstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['destination_warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['source_warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_transfers_date'), 'inventory_transfers', ['date'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_destination_warehouse_id'), 'inventory_transfers', ['destination_warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_source_warehouse_id'), 'inventory_transfers', ['source_warehouse_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_status'), 'inventory_transfers', ['status'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_tenant_id'), 'inventory_transfers', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfers_transfer_number'), 'inventory_transfers', ['transfer_number'], unique=False)

    # 10. inventory_transfer_lines
    op.create_table('inventory_transfer_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('inventory_transfer_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inventory_transfer_id'], ['inventory_transfers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_transfer_lines_inventory_transfer_id'), 'inventory_transfer_lines', ['inventory_transfer_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfer_lines_material_id'), 'inventory_transfer_lines', ['material_id'], unique=False)
    op.create_index(op.f('ix_inventory_transfer_lines_tenant_id'), 'inventory_transfer_lines', ['tenant_id'], unique=False)

    # 11. inventory_adjustments
    op.create_table('inventory_adjustments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('adjustment_number', sa.String(length=100), nullable=False),
        sa.Column('warehouse_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'POSTED', 'CANCELLED', name='inventoryadjustmentstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouses.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_adjustments_adjustment_number'), 'inventory_adjustments', ['adjustment_number'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_date'), 'inventory_adjustments', ['date'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_status'), 'inventory_adjustments', ['status'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_tenant_id'), 'inventory_adjustments', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_inventory_adjustments_warehouse_id'), 'inventory_adjustments', ['warehouse_id'], unique=False)

    # 12. inventory_adjustment_lines
    op.create_table('inventory_adjustment_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('inventory_adjustment_id', sa.UUID(), nullable=False),
        sa.Column('material_id', sa.UUID(), nullable=False),
        sa.Column('adjustment_type', sa.Enum('IN', 'OUT', name='adjustmenttype'), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('unit_cost', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by_id', sa.UUID(), nullable=True),
        sa.Column('updated_by_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['inventory_adjustment_id'], ['inventory_adjustments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['updated_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inventory_adjustment_lines_inventory_adjustment_id'), 'inventory_adjustment_lines', ['inventory_adjustment_id'], unique=False)
    op.create_index(op.f('ix_inventory_adjustment_lines_material_id'), 'inventory_adjustment_lines', ['material_id'], unique=False)
    op.create_index(op.f('ix_inventory_adjustment_lines_tenant_id'), 'inventory_adjustment_lines', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('inventory_adjustment_lines')
    op.drop_table('inventory_adjustments')
    op.execute('DROP TYPE IF EXISTS inventoryadjustmentstatus;')
    op.execute('DROP TYPE IF EXISTS adjustmenttype;')
    
    op.drop_table('inventory_transfer_lines')
    op.drop_table('inventory_transfers')
    op.execute('DROP TYPE IF EXISTS inventorytransferstatus;')
    
    op.drop_table('material_issue_lines')
    op.drop_table('material_issues')
    op.execute('DROP TYPE IF EXISTS materialissuestatus;')
    
    op.drop_table('goods_receipt_lines')
    op.drop_table('goods_receipts')
    op.execute('DROP TYPE IF EXISTS goodsreceiptstatus;')
    
    op.drop_table('inventory_balances')
    op.drop_table('inventory_transactions')
    op.execute('DROP TYPE IF EXISTS transactiontype;')
    
    op.drop_table('warehouses')
    op.execute('DROP TYPE IF EXISTS warehousetype;')
    
    op.drop_table('materials')
