"""Multi-tenant Foundation

Revision ID: 001
Revises: 
Create Date: 2026-08-11 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Tenants
    op.create_table(
        'tenants',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Legal Entities
    op.create_table(
        'legal_entities',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tax_id', sa.String(length=100), nullable=True),
        sa.Column('registration_number', sa.String(length=100), nullable=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_entities_tenant_id'), 'legal_entities', ['tenant_id'], unique=False)

    # Branches
    op.create_table(
        'branches',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('legal_entity_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=True),
        sa.Column('updated_by', sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(['legal_entity_id'], ['legal_entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_branches_tenant_id'), 'branches', ['tenant_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_branches_tenant_id'), table_name='branches')
    op.drop_table('branches')
    op.drop_index(op.f('ix_legal_entities_tenant_id'), table_name='legal_entities')
    op.drop_table('legal_entities')
    op.drop_table('tenants')
