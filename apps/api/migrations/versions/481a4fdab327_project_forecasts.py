"""project_forecasts

Revision ID: 481a4fdab327
Revises: 7f1ceb213a0d
Create Date: 2026-08-12 00:30:11.475663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '481a4fdab327'
down_revision: Union[str, None] = '7f1ceb213a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('project_forecasts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('project_id', sa.Uuid(), nullable=False),
        sa.Column('forecast_number', sa.String(length=100), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_forecasts_project_id'), 'project_forecasts', ['project_id'], unique=False)

    op.create_table('project_forecast_lines',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('forecast_id', sa.Uuid(), nullable=False),
        sa.Column('cost_code_id', sa.Uuid(), nullable=False),
        sa.Column('etc_amount', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['cost_code_id'], ['cost_codes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['forecast_id'], ['project_forecasts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_forecast_lines_cost_code_id'), 'project_forecast_lines', ['cost_code_id'], unique=False)
    op.create_index(op.f('ix_project_forecast_lines_forecast_id'), 'project_forecast_lines', ['forecast_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_project_forecast_lines_forecast_id'), table_name='project_forecast_lines')
    op.drop_index(op.f('ix_project_forecast_lines_cost_code_id'), table_name='project_forecast_lines')
    op.drop_table('project_forecast_lines')
    op.drop_index(op.f('ix_project_forecasts_project_id'), table_name='project_forecasts')
    op.drop_table('project_forecasts')
