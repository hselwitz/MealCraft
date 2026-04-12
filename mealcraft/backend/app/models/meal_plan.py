import uuid
from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import (
    VARCHAR,
    DATE,
    Integer,
    TIMESTAMP,
    Text,
    Enum as SAEnum,
    ForeignKey,
    Numeric,
    JSON,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    start_date: Mapped[str] = mapped_column(DATE, nullable=False)
    end_date: Mapped[str] = mapped_column(DATE, nullable=False)
    calorie_target: Mapped[int | None] = mapped_column(Integer, nullable=True, default=2500)
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "active", "archived", name="plan_status"), nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)
    generation_prompt_hash: Mapped[str | None] = mapped_column(VARCHAR(64), nullable=True)
    batch_components: Mapped[list | None] = mapped_column(JSON, nullable=True)

    slots: Mapped[list["MealSlot"]] = relationship(
        "MealSlot", back_populates="plan", cascade="all, delete-orphan"
    )
    grocery_lists: Mapped[list["GroceryList"]] = relationship(
        "GroceryList", back_populates="plan", cascade="all, delete-orphan"
    )


class MealSlot(Base):
    __tablename__ = "meal_slots"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    meal_plan_id: Mapped[str] = mapped_column(
        VARCHAR(36), ForeignKey("meal_plans.id"), nullable=False
    )
    date: Mapped[str] = mapped_column(DATE, nullable=False)
    meal_type: Mapped[str] = mapped_column(
        SAEnum("breakfast", "lunch", "dinner", "snack", name="meal_type"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        SAEnum("planned", "cooked", "skipped", "eating_out", name="slot_status"),
        nullable=False,
        default="planned",
    )
    recipe_id: Mapped[str | None] = mapped_column(
        VARCHAR(36), ForeignKey("recipes.id"), nullable=True
    )
    servings: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan: Mapped["MealPlan"] = relationship("MealPlan", back_populates="slots")
    recipe: Mapped["Recipe | None"] = relationship("Recipe", foreign_keys=[recipe_id])
    leftovers: Mapped[list["Leftover"]] = relationship(
        "Leftover", foreign_keys="[Leftover.meal_slot_id]", back_populates="meal_slot"
    )
    feedback: Mapped[list["MealFeedback"]] = relationship("MealFeedback", back_populates="slot")


class MealFeedback(Base):
    __tablename__ = "meal_feedback"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    meal_slot_id: Mapped[str | None] = mapped_column(
        VARCHAR(36), ForeignKey("meal_slots.id"), nullable=True
    )
    recipe_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("recipes.id"), nullable=False)
    rating: Mapped[str] = mapped_column(
        SAEnum("thumbs_up", "thumbs_down", name="feedback_rating"), nullable=False
    )
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)

    slot: Mapped["MealSlot"] = relationship("MealSlot", back_populates="feedback")
    recipe: Mapped["Recipe"] = relationship("Recipe")
