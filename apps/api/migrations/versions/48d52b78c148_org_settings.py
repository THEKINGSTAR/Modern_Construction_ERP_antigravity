"""org_settings

Revision ID: 48d52b78c148
Revises: 002
Create Date: 2026-08-11 21:03:12.439822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48d52b78c148'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # currencies
    op.create_table(
        'currencies',
        sa.Column('code', sa.String(length=3), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('code')
    )
    op.create_index(op.f('ix_currencies_code'), 'currencies', ['code'], unique=False)

    # exchange_rates
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('from_currency_code', sa.String(length=3), nullable=False),
        sa.Column('to_currency_code', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(precision=18, scale=6), nullable=False),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_to', sa.DateTime(), nullable=True),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['from_currency_code'], ['currencies.code'], ),
        sa.ForeignKeyConstraint(['to_currency_code'], ['currencies.code'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # fiscal_years
    op.create_table(
        'fiscal_years',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # accounting_periods
    op.create_table(
        'accounting_periods',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fiscal_year_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_closed', sa.Boolean(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['fiscal_year_id'], ['fiscal_years.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # tenant_settings
    op.create_table(
        'tenant_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('base_currency_code', sa.String(length=3), nullable=False),
        sa.Column('default_locale', sa.String(length=20), nullable=False),
        sa.Column('default_timezone', sa.String(length=50), nullable=False),
        sa.Column('default_date_format', sa.String(length=20), nullable=False),
        sa.Column('default_number_format', sa.String(length=20), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['base_currency_code'], ['currencies.code'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('tenant_settings')
    op.drop_table('accounting_periods')
    op.drop_table('fiscal_years')
    op.drop_table('exchange_rates')
    op.drop_index(op.f('ix_currencies_code'), table_name='currencies')
    op.drop_table('currencies')
