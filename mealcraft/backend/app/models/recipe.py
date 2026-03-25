import uuid
from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import (
    VARCHAR, Integer, TIMESTAMP, Text, Enum as SAEnum,
    ForeignKey, Numeric, JSON, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    prep_time_min: Mapped[int] = mapped_column(Integer, nullable=False)
    cook_time_min: Mapped[int] = mapped_column(Integer, nullable=False)
    total_time_min: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[str] = mapped_column(
        SAEnum("easy", "medium", "hard", name="difficulty_level"),
        nullable=False
    )
    servings: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    calories_per_serving: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)

    steps: Mapped[list["RecipeStep"]] = relationship(
        "RecipeStep", back_populates="recipe", cascade="all, delete-orphan",
        order_by="RecipeStep.step_number"
    )
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan"
    )


class RecipeStep(Base):
    __tablename__ = "recipe_steps"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    recipe_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("recipes.id"), nullable=False)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="steps")
