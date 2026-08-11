"""procurement

Revision ID: 2cdf55200112
Revises: 452f2f357a9e
Create Date: 2026-08-11 23:40:32.609660

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2cdf55200112'
down_revision: Union[str, None] = '452f2f357a9e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
