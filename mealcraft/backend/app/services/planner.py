"""Orchestrates LLM plan generation and persistence."""

import logging

from app.llm.client import LLMClient
from app.models.ingredient import Ingredient, RecipeIngredient
from app.models.meal_plan import MealPlan, MealSlot
from app.models.recipe import Recipe, RecipeStep
from app.services.optimizer import score_weekly_time
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


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

        home_slots = [s for s in slots if s.status == "planned" and s.meal_type != "snack"]

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
        total = len(fillable)

        for i, slot_plan in enumerate(fillable, 1):
            db_slot = slot_map[(slot_plan.date, slot_plan.meal_type)]
            yield f"Generating recipe {i}/{total}: {slot_plan.meal_concept}..."

            constraints = {
                "target_servings": float(db_slot.servings),
                "calorie_target": plan.calorie_target,
                "max_difficulty": preferences.get("max_difficulty", "medium"),
                "dietary_restrictions": preferences.get("dietary_restrictions", []),
            }
            if slot_plan.batch_component:
                constraints["batch_component"] = slot_plan.batch_component

            recipe = await self._generate_and_save_recipe(slot_plan.meal_concept, constraints)
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
            "calorie_target": plan.calorie_target,
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
