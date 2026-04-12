"""Add batch_components to meal_plans

Revision ID: 004
Revises: 003
Create Date: 2026-04-11 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meal_plans", sa.Column("batch_components", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("meal_plans", "batch_components")
