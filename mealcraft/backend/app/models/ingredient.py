import uuid

from app.db import Base
from sqlalchemy import VARCHAR, Integer, Enum as SAEnum, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    canonical_name: Mapped[str] = mapped_column(VARCHAR(255), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(
        SAEnum(
            "produce",
            "protein",
            "dairy",
            "grain",
            "pantry",
            "spice",
            "other",
            name="ingredient_category",
        ),
        nullable=False,
        default="other",
    )
    default_unit: Mapped[str] = mapped_column(VARCHAR(50), nullable=False, default="")
    shelf_life_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(
        "RecipeIngredient", back_populates="ingredient"
    )
    grocery_items: Mapped[list["GroceryItem"]] = relationship(
        "GroceryItem", back_populates="ingredient"
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    recipe_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("recipes.id"), nullable=False)
    ingredient_id: Mapped[str] = mapped_column(
        VARCHAR(36), ForeignKey("ingredients.id"), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    unit: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    prep_note: Mapped[str | None] = mapped_column(VARCHAR(255), nullable=True)
    is_optional: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient: Mapped["Ingredient"] = relationship(
        "Ingredient", back_populates="recipe_ingredients"
    )
