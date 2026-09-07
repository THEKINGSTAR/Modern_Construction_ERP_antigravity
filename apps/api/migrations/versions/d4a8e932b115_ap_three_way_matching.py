"""ap three way matching and line enhancements

Revision ID: d4a8e932b115
Revises: 3685683c7679
Create Date: 2026-09-08 00:08:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd4a8e932b115'
down_revision: Union[str, None] = '3685683c7679'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to ap_invoices
    op.add_column('ap_invoices', sa.Column('purchase_order_id', sa.Uuid(), nullable=True))
    op.add_column('ap_invoices', sa.Column('goods_receipt_id', sa.Uuid(), nullable=True))
    op.add_column('ap_invoices', sa.Column('subtotal', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))
    op.add_column('ap_invoices', sa.Column('tax_amount', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))
    op.add_column('ap_invoices', sa.Column('matching_status', sa.String(length=50), server_default='UNMATCHED', nullable=False))

    op.create_foreign_key(
        'fk_ap_invoices_purchase_order_id',
        'ap_invoices', 'purchase_orders',
        ['purchase_order_id'], ['id']
    )
    op.create_foreign_key(
        'fk_ap_invoices_goods_receipt_id',
        'ap_invoices', 'goods_receipts',
        ['goods_receipt_id'], ['id']
    )

    # 2. Add columns to ap_invoice_lines
    op.add_column('ap_invoice_lines', sa.Column('purchase_order_line_id', sa.Uuid(), nullable=True))
    op.add_column('ap_invoice_lines', sa.Column('goods_receipt_line_id', sa.Uuid(), nullable=True))
    op.add_column('ap_invoice_lines', sa.Column('material_id', sa.Uuid(), nullable=True))
    op.add_column('ap_invoice_lines', sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), server_default='0.0', nullable=False))
    op.add_column('ap_invoice_lines', sa.Column('tax_amount', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))

    op.create_foreign_key(
        'fk_ap_invoice_lines_po_line_id',
        'ap_invoice_lines', 'purchase_order_lines',
        ['purchase_order_line_id'], ['id']
    )
    op.create_foreign_key(
        'fk_ap_invoice_lines_grn_line_id',
        'ap_invoice_lines', 'goods_receipt_lines',
        ['goods_receipt_line_id'], ['id']
    )
    op.create_foreign_key(
        'fk_ap_invoice_lines_material_id',
        'ap_invoice_lines', 'materials',
        ['material_id'], ['id']
    )


def downgrade() -> None:
    # Drop ap_invoice_lines foreign keys and columns
    op.drop_constraint('fk_ap_invoice_lines_material_id', 'ap_invoice_lines', type_='foreignkey')
    op.drop_constraint('fk_ap_invoice_lines_grn_line_id', 'ap_invoice_lines', type_='foreignkey')
    op.drop_constraint('fk_ap_invoice_lines_po_line_id', 'ap_invoice_lines', type_='foreignkey')
    op.drop_column('ap_invoice_lines', 'tax_amount')
    op.drop_column('ap_invoice_lines', 'tax_rate')
    op.drop_column('ap_invoice_lines', 'material_id')
    op.drop_column('ap_invoice_lines', 'goods_receipt_line_id')
    op.drop_column('ap_invoice_lines', 'purchase_order_line_id')

    # Drop ap_invoices foreign keys and columns
    op.drop_constraint('fk_ap_invoices_goods_receipt_id', 'ap_invoices', type_='foreignkey')
    op.drop_constraint('fk_ap_invoices_purchase_order_id', 'ap_invoices', type_='foreignkey')
    op.drop_column('ap_invoices', 'matching_status')
    op.drop_column('ap_invoices', 'tax_amount')
    op.drop_column('ap_invoices', 'subtotal')
    op.drop_column('ap_invoices', 'goods_receipt_id')
    op.drop_column('ap_invoices', 'purchase_order_id')
