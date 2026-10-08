"""7-step grocery list generation pipeline."""

import logging

from app.llm.client import LLMClient
from app.models.grocery import GroceryList, GroceryItem
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.leftover import Leftover
from app.models.meal_plan import MealSlot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

# Common pantry staples assumed to always be on hand
DEFAULT_PANTRY_STAPLES = [
    "salt",
    "black pepper",
    "olive oil",
    "vegetable oil",
    "sugar",
    "all-purpose flour",
    "baking soda",
    "baking powder",
    "water",
]


class GroceryService:
    def __init__(self, db: AsyncSession, llm: LLMClient):
        self.db = db
        self.llm = llm

    async def generate_for_plan(
        self,
        plan_id: str,
        pantry_staples: list[str] | None = None,
        ingredient_overlap: str = "medium",
        prep_plan_ingredients: list[dict] | None = None,
        selected_slots: list | None = None,
        scope: dict | None = None,
    ) -> GroceryList:
        """Run the 7-step grocery generation pipeline."""
        if pantry_staples is None:
            pantry_staples = DEFAULT_PANTRY_STAPLES

        # Step 1: Collect RecipeIngredients from active slots
        slots_result = await self.db.execute(
            select(MealSlot)
            .where(MealSlot.meal_plan_id == plan_id, MealSlot.status == "planned")
            .options(selectinload(MealSlot.recipe))
        )
        slots = selected_slots if selected_slots is not None else slots_result.scalars().all()

        raw_ingredients: list[dict] = []
        for slot in slots:
            if not slot.recipe:
                continue
            recipe = slot.recipe
            # Load recipe ingredients
            ri_result = await self.db.execute(
                select(RecipeIngredient)
                .where(RecipeIngredient.recipe_id == recipe.id)
                .options(selectinload(RecipeIngredient.ingredient))
            )
            recipe_ingredients = ri_result.scalars().all()

            scale = float(slot.servings) / float(recipe.servings) if recipe.servings else 1.0
            for ri in recipe_ingredients:
                if ri.is_optional:
                    continue
                raw_ingredients.append(
                    {
                        "ingredient_id": ri.ingredient_id,
                        "ingredient_name": ri.ingredient.canonical_name,
                        "quantity": float(ri.quantity) * scale,
                        "unit": ri.unit,
                        "category": ri.ingredient.category,
                    }
                )

        # Step 2: Add prep plan ingredients (source of truth for batch cooking)
        if prep_plan_ingredients:
            for ing in prep_plan_ingredients:
                raw_ingredients.append(
                    {
                        "ingredient_id": None,
                        "ingredient_name": ing["ingredient_name"],
                        "quantity": float(ing["quantity"]),
                        "unit": ing["unit"],
                        "category": "other",
                    }
                )

        # Step 3: Subtract leftover inventory
        leftovers_result = await self.db.execute(
            select(Leftover)
            .join(MealSlot, Leftover.meal_slot_id == MealSlot.id)
            .where(MealSlot.meal_plan_id == plan_id, Leftover.status == "available")
            .options(selectinload(Leftover.recipe))
        )
        available_leftovers = leftovers_result.scalars().all()

        leftover_inventory = []
        for lv in available_leftovers:
            if lv.recipe:
                leftover_inventory.append(
                    {
                        "ingredient_name": lv.recipe.title,
                        "quantity": float(lv.remaining_servings),
                        "unit": "servings",
                    }
                )

        # Step 4: Subtract pantry staples
        if selected_slots is not None:
            # A leftover dish only replaces groceries when explicitly scheduled as such.
            leftover_inventory = []
        pantry_set = {s.lower().strip() for s in pantry_staples}

        # Step 5: Aggregate by canonical ingredient
        aggregated: dict[tuple[str, str], dict] = {}
        for item in raw_ingredients:
            name = item["ingredient_name"].lower()
            key = (name, item["unit"])
            if name in pantry_set:
                continue
            if key in aggregated:
                if aggregated[key]["unit"] == item["unit"]:
                    aggregated[key]["quantity"] += item["quantity"]
            else:
                aggregated[key] = {
                    "ingredient_name": name,
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "ingredient_id": item["ingredient_id"],
                    "category": item.get("category", "other"),
                }

        # Step 6: Organize by store section (category -> section mapping)
        category_to_section = {
            "produce": "produce",
            "protein": "meat",
            "dairy": "dairy",
            "grain": "pantry",
            "pantry": "pantry",
            "spice": "pantry",
            "other": "other",
        }

        for item in aggregated.values():
            item["store_section"] = category_to_section.get(item.get("category", "other"), "other")

        # Step 7: LLM post-processing for purchasable quantities
        if aggregated:
            grocery_out = await self.llm.generate_grocery_list(
                ingredients=list(aggregated.values()),
                pantry=pantry_staples,
                leftovers=leftover_inventory,
                ingredient_overlap=ingredient_overlap,
            )
        else:
            from app.llm.schemas import GroceryListOutput

            grocery_out = GroceryListOutput(items=[])

        # Persist to DB
        previous = await self.db.scalar(select(GroceryList).where(GroceryList.meal_plan_id == plan_id)
                                        .order_by(GroceryList.generated_at.desc()).limit(1))
        checked = {}
        if scope and previous and previous.scope and all(previous.scope.get(k) == scope.get(k) for k in ("start_date", "end_date")):
            previous_items = await self.db.execute(select(GroceryItem).where(GroceryItem.grocery_list_id == previous.id)
                                                  .options(selectinload(GroceryItem.ingredient)))
            checked = {(i.ingredient.canonical_name, i.unit): float(i.quantity)
                       for i in previous_items.scalars() if i.checked}
        grocery_list = GroceryList(meal_plan_id=plan_id, scope=scope)
        self.db.add(grocery_list)
        await self.db.flush()

        for item in grocery_out.items:
            # Get or create ingredient
            ing_result = await self.db.execute(
                select(Ingredient).where(Ingredient.canonical_name == item.ingredient_name.lower())
            )
            ingredient = ing_result.scalar_one_or_none()
            if not ingredient:
                ingredient = Ingredient(canonical_name=item.ingredient_name.lower())
                self.db.add(ingredient)
                await self.db.flush()

            grocery_item = GroceryItem(
                grocery_list_id=grocery_list.id,
                ingredient_id=ingredient.id,
                quantity=item.quantity,
                unit=item.unit,
                store_section=item.store_section,
                checked=checked.get((ingredient.canonical_name, item.unit), -1) >= item.quantity,
            )
            self.db.add(grocery_item)

        await self.db.flush()
        return grocery_list
