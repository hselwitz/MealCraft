"""Leftover management: expiry estimation and status management."""

import logging
from datetime import date, timedelta

from app.models.leftover import Leftover
from app.models.meal_plan import MealSlot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# Default shelf life by ingredient category if not specified
DEFAULT_SHELF_LIFE_BY_CATEGORY = {
    "produce": 5,
    "protein": 3,
    "dairy": 7,
    "grain": 14,
    "pantry": 365,
    "spice": 365,
    "other": 4,
}

# Default shelf life for cooked leftovers
COOKED_LEFTOVER_SHELF_LIFE_DAYS = 4


class LeftoverService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def estimate_expiry(self, stored_date: str, recipe_id: str | None = None) -> str:
        """Estimate expiry date for a leftover."""
        try:
            stored = date.fromisoformat(stored_date)
        except ValueError:
            stored = date.today()

        # Look at recipe ingredients to estimate shelf life
        shelf_life = COOKED_LEFTOVER_SHELF_LIFE_DAYS

        if recipe_id:
            from app.models.ingredient import RecipeIngredient

            ri_result = await self.db.execute(
                select(RecipeIngredient)
                .where(RecipeIngredient.recipe_id == recipe_id)
                .options(selectinload(RecipeIngredient.ingredient))
            )
            recipe_ingredients = ri_result.scalars().all()

            if recipe_ingredients:
                min_shelf_life = min(
                    (
                        ri.ingredient.shelf_life_days
                        or DEFAULT_SHELF_LIFE_BY_CATEGORY.get(
                            ri.ingredient.category, COOKED_LEFTOVER_SHELF_LIFE_DAYS
                        )
                    )
                    for ri in recipe_ingredients
                )
                # Cooked food lasts min(cooked shelf life, shortest ingredient)
                shelf_life = min(COOKED_LEFTOVER_SHELF_LIFE_DAYS, min_shelf_life)

        expiry = stored + timedelta(days=shelf_life)
        return expiry.isoformat()

    async def get_expiry_status(self, leftover: Leftover) -> str:
        """Return 'fresh', 'expiring_soon', or 'expired'."""
        try:
            expiry = date.fromisoformat(str(leftover.expiry_date))
        except (ValueError, TypeError):
            return "fresh"

        today = date.today()
        days_until_expiry = (expiry - today).days

        if days_until_expiry < 0:
            return "expired"
        elif days_until_expiry <= 1:
            return "expiring_soon"
        else:
            return "fresh"

    async def mark_expired_leftovers(self) -> int:
        """Mark all expired leftovers as discarded. Returns count updated."""
        today = date.today().isoformat()
        result = await self.db.execute(
            select(Leftover).where(
                Leftover.status == "available",
                Leftover.expiry_date < today,
            )
        )
        leftovers = result.scalars().all()

        for lv in leftovers:
            lv.status = "discarded"
            self.db.add(lv)

        await self.db.flush()
        return len(leftovers)
