import uuid

from app.db import Base
from sqlalchemy import (
    VARCHAR, DATE, Enum as SAEnum, ForeignKey, Numeric
)
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Leftover(Base):
    __tablename__ = "leftovers"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    meal_slot_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("meal_slots.id"), nullable=False)
    recipe_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("recipes.id"), nullable=False)
    remaining_servings: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    stored_date: Mapped[str] = mapped_column(DATE, nullable=False)
    expiry_date: Mapped[str] = mapped_column(DATE, nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("available", "used", "discarded", name="leftover_status"),
        nullable=False, default="available"
    )
    used_in_slot_id: Mapped[str | None] = mapped_column(
        VARCHAR(36), ForeignKey("meal_slots.id"), nullable=True
    )

    meal_slot: Mapped["MealSlot"] = relationship(
        "MealSlot", foreign_keys=[meal_slot_id], back_populates="leftovers"
    )
    recipe: Mapped["Recipe"] = relationship("Recipe")
    used_in_slot: Mapped["MealSlot | None"] = relationship(
        "MealSlot", foreign_keys=[used_in_slot_id]
    )
