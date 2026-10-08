"""Dinner discovery and a plan-independent personal repertoire."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.llm.client import LLMClient, get_llm_client
from app.models.recipe import Recipe
from app.models.repertoire import RepertoireMeal
from app.models.settings import AppSettings
from app.routers.settings import public_settings
from app.routers.recipes import _load_recipe, _recipe_to_out
from app.schemas.discovery import (
    DiscoveryRequest, DinnerIdeas, DinnerRecipeRequest,
    RepertoireCreate, RepertoireUpdate, RepertoireOut,
)
from app.services.planner import PlannerService

router = APIRouter(tags=["discovery"])


async def user_settings(db):
    row = await db.get(AppSettings, "default")
    return public_settings(row.data if row else {})


@router.get("/repertoire", response_model=list[RepertoireOut])
async def list_repertoire(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RepertoireMeal).order_by(desc(RepertoireMeal.created_at)).limit(500))
    return result.scalars().all()


@router.post("/repertoire", response_model=RepertoireOut, status_code=201)
async def add_familiar_meal(body: RepertoireCreate, db: AsyncSession = Depends(get_db)):
    if not body.title.strip():
        raise HTTPException(422, "Give your meal a name.")
    meal = RepertoireMeal(title=body.title.strip(), notes=body.notes.strip(), familiar=True, saved=True)
    db.add(meal)
    await db.flush()
    return meal


def apply_feedback(meal, body):
    for field in ("saved", "verdict", "easy_enough", "notes"):
        if field in body.model_fields_set:
            value = getattr(body, field)
            if field in ("saved", "notes") and value is None:
                continue
            setattr(meal, field, value)
    if body.cooked:
        meal.cooked_count += 1
        meal.last_cooked_at = datetime.now(timezone.utc)


@router.patch("/repertoire/{meal_id}", response_model=RepertoireOut)
async def update_meal(meal_id: str, body: RepertoireUpdate, db: AsyncSession = Depends(get_db)):
    meal = await db.get(RepertoireMeal, meal_id)
    if not meal:
        raise HTTPException(404, "Meal not found.")
    apply_feedback(meal, body)
    await db.flush()
    return meal


@router.put("/repertoire/recipes/{recipe_id}", response_model=RepertoireOut)
async def update_recipe_memory(recipe_id: str, body: RepertoireUpdate, db: AsyncSession = Depends(get_db)):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(404, "Recipe not found.")
    meal = await db.scalar(select(RepertoireMeal).where(RepertoireMeal.recipe_id == recipe_id))
    if not meal:
        meal = RepertoireMeal(recipe_id=recipe_id, title=recipe.title, notes="", saved=False,
                              familiar=False, cooked_count=0)
        db.add(meal)
    apply_feedback(meal, body)
    await db.flush()
    return meal


@router.post("/discover/ideas", response_model=DinnerIdeas)
async def discover(body: DiscoveryRequest, db: AsyncSession = Depends(get_db), llm: LLMClient = Depends(get_llm_client)):
    meals = await list_repertoire(db)
    selected = None
    if body.familiar_meal_id:
        selected = await db.get(RepertoireMeal, body.familiar_meal_id)
        if not selected:
            raise HTTPException(404, "The selected familiar meal was not found.")
    context = [RepertoireOut.model_validate(meal).model_dump(mode="json") for meal in meals
               if meal.familiar or meal.saved or meal.cooked_count or meal.verdict or meal.easy_enough is not None]
    if body.planning_start_date and body.planning_end_date:
        from app.routers.workflow import selected_meals, planning_window
        from app.models.meal_plan import MealPlan
        plan = await db.scalar(select(MealPlan).where(MealPlan.status.in_(["active", "draft"])).order_by(desc(MealPlan.created_at)).limit(1))
        if plan:
            slots = await selected_meals(db, plan.id, planning_window(body.planning_start_date, body.planning_end_date))
            context += [{"title": slot.recipe.title, "scheduled": True, "date": str(slot.date),
                         "servings": float(slot.servings),
                         "ingredients": [i.ingredient.canonical_name for i in slot.recipe.recipe_ingredients]}
                        for slot in slots]
    try:
        return await llm.suggest_dinners(body, context, await user_settings(db), selected)
    except ValueError as error:
        raise HTTPException(502, str(error)) from error


@router.post("/discover/recipe")
async def cook_idea(body: DinnerRecipeRequest, db: AsyncSession = Depends(get_db), llm: LLMClient = Depends(get_llm_client)):
    prefs = await user_settings(db)
    constraints = {
        "cooking_mode": "dinner", "max_active_min": body.max_active_min,
        "target_servings": prefs["defaultServings"], "max_difficulty": "easy",
        "dietary_restrictions": prefs["dietaryRestrictions"],
        "available_ingredients_and_request": body.request,
        "convenience_tip": body.idea.convenience_tip, "cookware": body.idea.cleanup,
        "estimated_elapsed_min": body.idea.total_time_min,
        "suggested_extra_ingredients": body.idea.extra_ingredients,
    }
    concept = f"{body.idea.title}: {body.idea.description}. {body.idea.familiar_connection}"
    try:
        output = await llm.generate_recipe(concept, constraints)
    except ValueError as error:
        raise HTTPException(502, str(error)) from error
    active_steps = [step for step in output.steps if step.is_active]
    if not output.steps or not output.ingredients or any(step.duration_min is None for step in active_steps):
        raise HTTPException(502, "The recipe was incomplete. Please try again.")
    active = sum(step.duration_min for step in active_steps)
    if active > body.max_active_min:
        raise HTTPException(502, "This recipe exceeded your hands-on budget. Please try another idea.")
    recipe = await PlannerService(db, llm)._save_recipe_output(output, concept)
    return _recipe_to_out(await _load_recipe(recipe.id, db))
