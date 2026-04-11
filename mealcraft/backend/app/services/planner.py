"""Orchestrates LLM plan generation and persistence."""

import logging
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.meal_plan import MealPlan, MealSlot
from app.models.recipe import Recipe, RecipeStep

logger = logging.getLogger(__name__)

# Hour (24h) after which a meal type is considered past and won't be regenerated
_MEAL_CUTOFF_HOUR: dict[str, int] = {
    "breakfast": 10,
    "lunch": 14,
    "dinner": 20,
}

_MEAL_CALORIE_FRACTION: dict[str, float] = {
    "breakfast": 0.25,
    "lunch": 0.30,
    "dinner": 0.40,
    "snack": 0.05,
}


def _meal_calorie_target(daily_target: int | None, meal_type: str) -> int | None:
    if not daily_target:
        return None
    fraction = _MEAL_CALORIE_FRACTION.get(meal_type, 0.33)
    return round(daily_target * fraction)


class PlannerService:
    def __init__(self, db: AsyncSession, llm: LLMClient):
        self.db = db
        self.llm = llm

    async def generate_plan(
        self,
        plan: MealPlan,
        preferences: dict,
        schedule: dict,
        leftovers: list,
        pantry: list,
    ):
        """Async generator: yields progress strings, then saves all recipes."""
        slots = (
            (await self.db.execute(select(MealSlot).where(MealSlot.meal_plan_id == plan.id)))
            .scalars()
            .all()
        )

        today = date.today()
        current_hour = datetime.now().hour
        home_slots = [
            s
            for s in slots
            if s.status == "planned"
            and s.meal_type != "snack"
            and s.date > today
            or (
                s.status == "planned"
                and s.meal_type != "snack"
                and s.date == today
                and current_hour < _MEAL_CUTOFF_HOUR.get(s.meal_type, 24)
            )
        ]

        slots_to_fill = [{"date": str(s.date), "meal_type": s.meal_type} for s in home_slots]

        prefs = {
            **preferences,
            "start_date": str(plan.start_date),
            "end_date": str(plan.end_date),
            "calorie_target": plan.calorie_target or 2500,
            "slots_to_fill": slots_to_fill,
        }

        yield "Planning your week with Claude..."
        weekly_plan = await self.llm.generate_weekly_plan(prefs, schedule, leftovers, pantry)
        logger.info(f"Generated weekly plan with {len(weekly_plan.meal_slots)} slots")

        slot_map = {(str(s.date), s.meal_type): s for s in home_slots}
        fillable = [sp for sp in weekly_plan.meal_slots if slot_map.get((sp.date, sp.meal_type))]

        batch_slots = [sp for sp in fillable if not sp.is_assembly]
        assembly_slots = [sp for sp in fillable if sp.is_assembly]
        total = len(fillable)
        i = 0

        # Pass 1: generate batch prep recipes first so we know exactly what gets cooked
        batch_recipes_data: list[dict] = []
        for slot_plan in batch_slots:
            i += 1
            db_slot = slot_map[(slot_plan.date, slot_plan.meal_type)]
            yield f"Generating recipe {i}/{total}: {slot_plan.meal_concept}..."
            constraints = {
                "target_servings": float(db_slot.servings),
                "calorie_target": _meal_calorie_target(plan.calorie_target, slot_plan.meal_type),
                "max_difficulty": preferences.get("max_difficulty", "medium"),
                "dietary_restrictions": preferences.get("dietary_restrictions", []),
            }
            recipe_out = await self.llm.generate_recipe(slot_plan.meal_concept, constraints)
            recipe = await self._save_recipe_output(recipe_out, slot_plan.meal_concept)
            db_slot.recipe_id = recipe.id
            self.db.add(db_slot)
            batch_recipes_data.append({
                "title": recipe_out.title,
                "ingredients": [ing.ingredient_name for ing in recipe_out.ingredients],
            })

        # Pass 2: generate assembly guides with the exact batch recipe ingredient lists
        for slot_plan in assembly_slots:
            i += 1
            db_slot = slot_map[(slot_plan.date, slot_plan.meal_type)]
            yield f"Generating recipe {i}/{total}: {slot_plan.meal_concept}..."
            constraints = {
                "target_servings": float(db_slot.servings),
                "calorie_target": _meal_calorie_target(plan.calorie_target, slot_plan.meal_type),
                "dietary_restrictions": preferences.get("dietary_restrictions", []),
            }
            recipe_out = await self.llm.generate_assembly_recipe(
                slot_plan.meal_concept, constraints, batch_recipes_data
            )
            recipe = await self._save_recipe_output(recipe_out, slot_plan.meal_concept)
            db_slot.recipe_id = recipe.id
            self.db.add(db_slot)

        await self.db.flush()
        yield "__DONE__"

    async def regenerate_slot_recipe(
        self, slot: MealSlot, plan: MealPlan, preferences: dict
    ) -> Recipe:
        """Regenerate recipe for a single slot."""
        constraints = {
            "target_servings": float(slot.servings),
            "calorie_target": _meal_calorie_target(plan.calorie_target, slot.meal_type),
            "max_difficulty": preferences.get("max_difficulty", "medium"),
            "dietary_restrictions": preferences.get("dietary_restrictions", []),
        }
        recipe = await self._generate_and_save_recipe(
            f"Regenerated {slot.meal_type} for {slot.date}", constraints
        )
        slot.recipe_id = recipe.id
        self.db.add(slot)
        await self.db.flush()
        return recipe

    async def _generate_and_save_recipe(self, concept: str, constraints: dict) -> Recipe:
        """Call LLM to generate recipe and persist to DB."""
        recipe_out = await self.llm.generate_recipe(concept, constraints)
        return await self._save_recipe_output(recipe_out, concept)

    async def _save_recipe_output(self, recipe_out, concept: str) -> Recipe:
        """Persist a RecipeOutput to the DB and return the Recipe ORM object."""
        recipe = Recipe(
            title=recipe_out.title,
            description=recipe_out.description,
            prep_time_min=recipe_out.prep_time_min,
            cook_time_min=recipe_out.cook_time_min,
            total_time_min=recipe_out.total_time_min,
            difficulty=recipe_out.difficulty,
            servings=recipe_out.servings,
            calories_per_serving=recipe_out.calories_per_serving,
            protein_g=recipe_out.protein_g,
            carbs_g=recipe_out.carbs_g,
            fat_g=recipe_out.fat_g,
            tags=recipe_out.tags,
            source_prompt=concept,
        )
        self.db.add(recipe)
        await self.db.flush()

        # Save steps
        for step_out in recipe_out.steps:
            step = RecipeStep(
                recipe_id=recipe.id,
                step_number=step_out.step_number,
                instruction=step_out.instruction,
                duration_min=step_out.duration_min,
                is_active=step_out.is_active,
            )
            self.db.add(step)

        # Save ingredients (canonicalize names)
        existing_names = await self._get_existing_ingredient_names()

        for ing_out in recipe_out.ingredients:
            canonical = await self.llm.canonicalize_ingredient(
                ing_out.ingredient_name, existing_names
            )
            ingredient = await self._get_or_create_ingredient(canonical)
            if canonical not in existing_names:
                existing_names.append(canonical)

            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                quantity=ing_out.quantity,
                unit=ing_out.unit,
                prep_note=ing_out.prep_note,
                is_optional=ing_out.is_optional,
            )
            self.db.add(ri)

        await self.db.flush()
        return recipe

    async def _get_existing_ingredient_names(self) -> list[str]:
        result = await self.db.execute(select(Ingredient.canonical_name))
        return list(result.scalars().all())

    async def _get_or_create_ingredient(self, canonical_name: str) -> Ingredient:
        result = await self.db.execute(
            select(Ingredient).where(Ingredient.canonical_name == canonical_name)
        )
        ingredient = result.scalar_one_or_none()
        if ingredient:
            return ingredient

        ingredient = Ingredient(canonical_name=canonical_name)
        self.db.add(ingredient)
        await self.db.flush()
        return ingredient
