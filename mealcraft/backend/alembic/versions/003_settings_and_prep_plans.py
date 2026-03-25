"""Add app_settings and prep_plans tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-25 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "prep_plans",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("meal_plan_id", sa.VARCHAR(36), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("data", sa.JSON, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("prep_plans")
    op.drop_table("app_settings")
