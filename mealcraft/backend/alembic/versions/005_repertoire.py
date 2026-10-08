"""Add a personal repertoire without changing existing recipes or plans."""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    table = op.create_table(
        "repertoire_meals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("recipe_id", sa.String(36), sa.ForeignKey("recipes.id", ondelete="CASCADE"), unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("familiar", sa.Boolean(), nullable=False),
        sa.Column("saved", sa.Boolean(), nullable=False),
        sa.Column("verdict", sa.String(20)),
        sa.Column("easy_enough", sa.Boolean()),
        sa.Column("cooked_count", sa.Integer(), nullable=False),
        sa.Column("last_cooked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Keep migration seed data independent of application code.
    meals = [
        ("usual-chicken", "Chili chicken with rice or quinoa", "Skin-on, bone-in chicken breast with white rice or quinoa and chili paste. Frozen bell peppers and onions when available."),
        ("usual-pasta", "Wheat pasta with chicken or beef", "Wheat pasta, olive oil, marinara, and chicken or ground beef."),
        ("usual-beef", "Beef patties, potato & sauerkraut", "Ground beef patties, a microwaved baked potato, and sauerkraut."),
    ]
    op.bulk_insert(table, [{"id": id, "title": title, "notes": notes, "familiar": True,
                          "saved": True, "cooked_count": 0, "created_at": datetime.now(timezone.utc)}
                         for id, title, notes in meals])


def downgrade():
    op.drop_table("repertoire_meals")
