"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-24 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("name", sa.VARCHAR(255), nullable=False),
        sa.Column("start_date", sa.DATE, nullable=False),
        sa.Column("end_date", sa.DATE, nullable=False),
        sa.Column("calorie_target", sa.Integer, nullable=True, default=2500),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "archived", name="plan_status"),
            nullable=False, default="draft",
        ),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
        sa.Column("generation_prompt_hash", sa.VARCHAR(64), nullable=True),
    )

    op.create_table(
        "recipes",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("title", sa.VARCHAR(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("prep_time_min", sa.Integer, nullable=False),
        sa.Column("cook_time_min", sa.Integer, nullable=False),
        sa.Column("total_time_min", sa.Integer, nullable=False),
        sa.Column(
            "difficulty",
            sa.Enum("easy", "medium", "hard", name="difficulty_level"),
            nullable=False,
        ),
        sa.Column("servings", sa.Numeric(5, 2), nullable=False),
        sa.Column("calories_per_serving", sa.Integer, nullable=True),
        sa.Column("protein_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("carbs_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("fat_g", sa.Numeric(6, 2), nullable=True),
        sa.Column("tags", sa.JSON, nullable=False, default=list),
        sa.Column("source_prompt", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )

    op.create_table(
        "meal_slots",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("meal_plan_id", sa.VARCHAR(36), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("date", sa.DATE, nullable=False),
        sa.Column(
            "meal_type",
            sa.Enum("breakfast", "lunch", "dinner", "snack", name="meal_type"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("planned", "cooked", "skipped", "eating_out", name="slot_status"),
            nullable=False, default="planned",
        ),
        sa.Column("recipe_id", sa.VARCHAR(36), sa.ForeignKey("recipes.id"), nullable=True),
        sa.Column("servings", sa.Numeric(5, 2), nullable=False, default=2.0),
        sa.Column("notes", sa.Text, nullable=True),
    )

    op.create_table(
        "recipe_steps",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("recipe_id", sa.VARCHAR(36), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("instruction", sa.Text, nullable=False),
        sa.Column("duration_min", sa.Integer, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
    )

    op.create_table(
        "ingredients",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("canonical_name", sa.VARCHAR(255), unique=True, nullable=False),
        sa.Column(
            "category",
            sa.Enum("produce", "protein", "dairy", "grain", "pantry", "spice", "other",
                    name="ingredient_category"),
            nullable=False, default="other",
        ),
        sa.Column("default_unit", sa.VARCHAR(50), nullable=False, default=""),
        sa.Column("shelf_life_days", sa.Integer, nullable=True),
    )

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("recipe_id", sa.VARCHAR(36), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("ingredient_id", sa.VARCHAR(36), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(8, 3), nullable=False),
        sa.Column("unit", sa.VARCHAR(50), nullable=False),
        sa.Column("prep_note", sa.VARCHAR(255), nullable=True),
        sa.Column("is_optional", sa.Boolean, nullable=False, default=False),
    )

    op.create_table(
        "leftovers",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("meal_slot_id", sa.VARCHAR(36), sa.ForeignKey("meal_slots.id"), nullable=False),
        sa.Column("recipe_id", sa.VARCHAR(36), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column("remaining_servings", sa.Numeric(5, 2), nullable=False),
        sa.Column("stored_date", sa.DATE, nullable=False),
        sa.Column("expiry_date", sa.DATE, nullable=False),
        sa.Column(
            "status",
            sa.Enum("available", "used", "discarded", name="leftover_status"),
            nullable=False, default="available",
        ),
        sa.Column("used_in_slot_id", sa.VARCHAR(36), sa.ForeignKey("meal_slots.id"), nullable=True),
    )

    op.create_table(
        "grocery_lists",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("meal_plan_id", sa.VARCHAR(36), sa.ForeignKey("meal_plans.id"), nullable=False),
        sa.Column("generated_at", sa.TIMESTAMP, nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "finalized", "ordered", name="grocery_status"),
            nullable=False, default="draft",
        ),
    )

    op.create_table(
        "grocery_items",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("grocery_list_id", sa.VARCHAR(36), sa.ForeignKey("grocery_lists.id"), nullable=False),
        sa.Column("ingredient_id", sa.VARCHAR(36), sa.ForeignKey("ingredients.id"), nullable=False),
        sa.Column("quantity", sa.Numeric(8, 3), nullable=False),
        sa.Column("unit", sa.VARCHAR(50), nullable=False),
        sa.Column(
            "store_section",
            sa.Enum("produce", "meat", "dairy", "bakery", "pantry", "frozen", "other",
                    name="store_section"),
            nullable=False, default="other",
        ),
        sa.Column("checked", sa.Boolean, nullable=False, default=False),
    )

    op.create_table(
        "meal_feedback",
        sa.Column("id", sa.VARCHAR(36), primary_key=True),
        sa.Column("meal_slot_id", sa.VARCHAR(36), sa.ForeignKey("meal_slots.id"), nullable=False),
        sa.Column("recipe_id", sa.VARCHAR(36), sa.ForeignKey("recipes.id"), nullable=False),
        sa.Column(
            "rating",
            sa.Enum("thumbs_up", "thumbs_down", name="feedback_rating"),
            nullable=False,
        ),
        sa.Column("tags", sa.JSON, nullable=True),
        sa.Column("note", sa.Text, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("meal_feedback")
    op.drop_table("grocery_items")
    op.drop_table("grocery_lists")
    op.drop_table("leftovers")
    op.drop_table("recipe_ingredients")
    op.drop_table("ingredients")
    op.drop_table("recipe_steps")
    op.drop_table("meal_slots")
    op.drop_table("recipes")
    op.drop_table("meal_plans")
