"""Make meal_feedback.meal_slot_id nullable

Revision ID: 002
Revises: 001
Create Date: 2026-03-24 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN directly, so we recreate the table.
    with op.batch_alter_table("meal_feedback") as batch_op:
        batch_op.alter_column(
            "meal_slot_id",
            existing_type=sa.VARCHAR(36),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("meal_feedback") as batch_op:
        batch_op.alter_column(
            "meal_slot_id",
            existing_type=sa.VARCHAR(36),
            nullable=False,
        )
