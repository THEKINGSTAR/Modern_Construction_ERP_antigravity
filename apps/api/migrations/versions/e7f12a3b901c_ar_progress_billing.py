"""ar progress billing and retainage enhancements

Revision ID: e7f12a3b901c
Revises: d4a8e932b115
Create Date: 2026-09-08 01:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e7f12a3b901c'
down_revision: Union[str, None] = 'd4a8e932b115'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to ar_invoices
    op.add_column('ar_invoices', sa.Column('contract_id', sa.Uuid(), nullable=True))
    op.add_column('ar_invoices', sa.Column('payment_application_id', sa.Uuid(), nullable=True))
    op.add_column('ar_invoices', sa.Column('subtotal', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))
    op.add_column('ar_invoices', sa.Column('tax_amount', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))
    op.add_column('ar_invoices', sa.Column('retention_amount', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))

    op.create_foreign_key(
        'fk_ar_invoices_contract_id',
        'ar_invoices', 'contracts',
        ['contract_id'], ['id']
    )
    op.create_foreign_key(
        'fk_ar_invoices_payment_application_id',
        'ar_invoices', 'client_payment_applications',
        ['payment_application_id'], ['id']
    )

    # 2. Add columns to ar_invoice_lines
    op.add_column('ar_invoice_lines', sa.Column('cost_code_id', sa.Uuid(), nullable=True))
    op.add_column('ar_invoice_lines', sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), server_default='0.0', nullable=False))
    op.add_column('ar_invoice_lines', sa.Column('tax_amount', sa.Numeric(precision=18, scale=4), server_default='0.0', nullable=False))

    op.create_foreign_key(
        'fk_ar_invoice_lines_cost_code_id',
        'ar_invoice_lines', 'cost_codes',
        ['cost_code_id'], ['id']
    )


def downgrade() -> None:
    # Drop ar_invoice_lines foreign keys and columns
    op.drop_constraint('fk_ar_invoice_lines_cost_code_id', 'ar_invoice_lines', type_='foreignkey')
    op.drop_column('ar_invoice_lines', 'tax_amount')
    op.drop_column('ar_invoice_lines', 'tax_rate')
    op.drop_column('ar_invoice_lines', 'cost_code_id')

    # Drop ar_invoices foreign keys and columns
    op.drop_constraint('fk_ar_invoices_payment_application_id', 'ar_invoices', type_='foreignkey')
    op.drop_constraint('fk_ar_invoices_contract_id', 'ar_invoices', type_='foreignkey')
    op.drop_column('ar_invoices', 'retention_amount')
    op.drop_column('ar_invoices', 'tax_amount')
    op.drop_column('ar_invoices', 'subtotal')
    op.drop_column('ar_invoices', 'payment_application_id')
    op.drop_column('ar_invoices', 'contract_id')
