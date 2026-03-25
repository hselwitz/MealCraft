import uuid
from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import (
    VARCHAR, TIMESTAMP, Enum as SAEnum, ForeignKey, Numeric, Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class GroceryList(Base):
    __tablename__ = "grocery_lists"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    meal_plan_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("meal_plans.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "finalized", "ordered", name="grocery_status"),
        nullable=False, default="draft"
    )

    plan: Mapped["MealPlan"] = relationship("MealPlan", back_populates="grocery_lists")
    items: Mapped[list["GroceryItem"]] = relationship(
        "GroceryItem", back_populates="grocery_list", cascade="all, delete-orphan"
    )


class GroceryItem(Base):
    __tablename__ = "grocery_items"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    grocery_list_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("grocery_lists.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("ingredients.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    unit: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    store_section: Mapped[str] = mapped_column(
        SAEnum("produce", "meat", "dairy", "bakery", "pantry", "frozen", "other",
               name="store_section"),
        nullable=False, default="other"
    )
    checked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    grocery_list: Mapped["GroceryList"] = relationship("GroceryList", back_populates="items")
    ingredient: Mapped["Ingredient"] = relationship("Ingredient", back_populates="grocery_items")
