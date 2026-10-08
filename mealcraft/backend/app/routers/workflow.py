"""One selection of meals drives planning, shopping, and coordinated prep."""
import hashlib
import json
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db import get_db
from app.models.meal_plan import MealPlan, MealSlot
from app.models.recipe import Recipe
from app.models.ingredient import RecipeIngredient
from app.models.grocery import GroceryList, GroceryItem
from app.models.prep_plan import PrepPlanRecord
from app.routers.grocery import _load_grocery_list, _grocery_list_to_out
from app.routers.discovery import user_settings
from app.schemas.workflow import PlanningWindow, ScheduleRecipe
from app.llm.client import get_llm_client, LLMClient
from app.services.grocery import GroceryService

router = APIRouter(prefix="/workflow", tags=["workflow"])


def planning_window(start_date, end_date):
    try:
        return PlanningWindow(start_date=start_date, end_date=end_date)
    except ValueError as error:
        raise HTTPException(422, "Choose an ordered planning window of at most 31 days.") from error


async def selected_meals(db, plan_id, window):
    if not await db.get(MealPlan, plan_id):
        raise HTTPException(404, "Plan not found.")
    result = await db.execute(select(MealSlot).where(
        MealSlot.meal_plan_id == plan_id, MealSlot.status == "planned",
        MealSlot.date >= window.start_date, MealSlot.date <= window.end_date,
        MealSlot.recipe_id.is_not(None)).order_by(MealSlot.date, MealSlot.meal_type)
        .options(selectinload(MealSlot.recipe).selectinload(Recipe.steps),
                 selectinload(MealSlot.recipe).selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)))
    return result.scalars().all()


def scope_for(slots, window):
    source = [(s.id, str(s.date), s.meal_type, s.recipe_id, float(s.servings)) for s in slots]
    return {**window.model_dump(mode="json"), "fingerprint": hashlib.sha256(json.dumps(source).encode()).hexdigest()}


def meals_for_prep(slots):
    return [{"slot_id": s.id, "recipe_id": s.recipe_id, "date": str(s.date), "meal_type": s.meal_type,
             "title": s.recipe.title, "servings": float(s.servings), "tags": s.recipe.tags,
             "ingredients": [{"ingredient_name": i.ingredient.canonical_name,
                              "quantity": float(i.quantity) * float(s.servings) / float(s.recipe.servings),
                              "unit": i.unit, "prep_note": i.prep_note, "optional": i.is_optional}
                             for i in s.recipe.recipe_ingredients],
             "steps": [{"instruction": step.instruction, "duration_min": step.duration_min, "active": step.is_active}
                       for step in s.recipe.steps]} for s in slots]


async def records(db, plan_id):
    prep = await db.scalar(select(PrepPlanRecord).where(PrepPlanRecord.meal_plan_id == plan_id).order_by(desc(PrepPlanRecord.created_at)).limit(1))
    grocery = await db.scalar(select(GroceryList).where(GroceryList.meal_plan_id == plan_id).order_by(desc(GroceryList.generated_at)).limit(1))
    return prep, grocery


@router.post("/meals")
async def schedule_recipe(body: ScheduleRecipe, db: AsyncSession = Depends(get_db)):
    if not await db.get(Recipe, body.recipe_id):
        raise HTTPException(404, "Recipe not found.")
    plan = await db.scalar(select(MealPlan).where(MealPlan.status.in_(["active", "draft"])).order_by(desc(MealPlan.created_at)).limit(1))
    if not plan:
        plan = MealPlan(name="My Meal Plan", start_date=body.date, end_date=body.date+timedelta(days=3650), status="active")
        db.add(plan)
        await db.flush()
    slot = await db.scalar(select(MealSlot).where(MealSlot.meal_plan_id == plan.id, MealSlot.date == body.date, MealSlot.meal_type == body.meal_type).limit(1))
    if slot and (slot.status != "planned" or slot.recipe_id not in (None, body.recipe_id)):
        raise HTTPException(409, "That meal slot is occupied. Choose another date or remove it in the calendar first.")
    if not slot:
        slot = MealSlot(meal_plan_id=plan.id, date=body.date, meal_type=body.meal_type, status="planned")
        db.add(slot)
    slot.recipe_id, slot.servings = body.recipe_id, body.servings
    plan.start_date = min(plan.start_date, body.date)
    plan.end_date = max(plan.end_date, body.date)
    await db.flush()
    return {"plan_id": plan.id, "slot_id": slot.id}


@router.get("/{plan_id}/summary")
async def summary(plan_id: str, start_date: date, end_date: date, db: AsyncSession = Depends(get_db)):
    window = planning_window(start_date, end_date)
    slots = await selected_meals(db, plan_id, window)
    scope = scope_for(slots, window)
    prep, grocery = await records(db, plan_id)
    shared = {}
    for s in slots:
        for name in {i.ingredient.canonical_name for i in s.recipe.recipe_ingredients if not i.is_optional}:
            shared[name] = shared.get(name, 0) + 1
    return {"scope": scope, "meal_count": len(slots), "servings": sum(float(s.servings) for s in slots),
            "shared_ingredients": [name for name, count in shared.items() if count > 1],
            "prep_ready": bool(prep and prep.data.get("scope") == scope),
            "shop_ready": bool(grocery and grocery.scope == scope),
            "prep": prep.data if prep and prep.data.get("scope") == scope else None}


@router.post("/{plan_id}/prep")
async def generate_prep(plan_id: str, body: PlanningWindow, db: AsyncSession = Depends(get_db), llm: LLMClient = Depends(get_llm_client)):
    slots = await selected_meals(db, plan_id, body)
    if not slots:
        raise HTTPException(400, "Add recipes to this planning window before generating prep.")
    try:
        output = await llm.coordinate_meals(meals_for_prep(slots), await user_settings(db), body)
    except ValueError as error:
        raise HTTPException(502, str(error)) from error
    data = output.model_dump()
    data.update(scope=scope_for(slots, body), completed_tasks=[])
    db.add(PrepPlanRecord(meal_plan_id=plan_id, data=data))
    await db.flush()
    # Assembly groceries depend on the raw ingredients in this exact prep session.
    if any("batch-assembly" in (s.recipe.tags or []) for s in slots):
        _, grocery = await records(db, plan_id)
        if grocery:
            grocery.scope = None
    return data


@router.get("/{plan_id}/prep")
async def current_prep(plan_id: str, start_date: date, end_date: date, db: AsyncSession = Depends(get_db)):
    window = planning_window(start_date, end_date)
    slots = await selected_meals(db, plan_id, window)
    prep, _ = await records(db, plan_id)
    if not prep:
        raise HTTPException(404, "No prep session yet.")
    return {**prep.data, "stale": prep.data.get("scope") != scope_for(slots, window)}


@router.post("/{plan_id}/shop")
async def generate_shop(plan_id: str, body: PlanningWindow, db: AsyncSession = Depends(get_db), llm: LLMClient = Depends(get_llm_client)):
    slots = await selected_meals(db, plan_id, body)
    if not slots:
        raise HTTPException(400, "Add recipes to this planning window before generating groceries.")
    prefs = await user_settings(db)
    scope = scope_for(slots, body)
    raw = None
    selected = slots
    if any("batch-assembly" in (s.recipe.tags or []) for s in slots):
        prep, _ = await records(db, plan_id)
        if not prep or prep.data.get("scope") != scope:
            raise HTTPException(400, "These meals use batch components. Generate the prep session first so the shopping list includes their raw ingredients.")
        raw = prep.data["grocery_ingredients"]
        selected = []  # Complete prep requirements replace assembly ingredients, not add to them.
    try:
        grocery = await GroceryService(db, llm).generate_for_plan(plan_id, prefs["pantryStaples"],
                    prefs["ingredientOverlap"], raw, selected_slots=selected, scope=scope)
    except ValueError as error:
        raise HTTPException(502, str(error)) from error
    return {"grocery_list_id": grocery.id, "status": "generated"}


@router.get("/{plan_id}/shop")
async def current_shop(plan_id: str, start_date: date, end_date: date, db: AsyncSession = Depends(get_db)):
    window = planning_window(start_date, end_date)
    slots = await selected_meals(db, plan_id, window)
    _, grocery = await records(db, plan_id)
    if not grocery:
        raise HTTPException(404, "No shopping list yet.")
    out = _grocery_list_to_out(await _load_grocery_list(grocery.id, db))
    out["stale"] = grocery.scope != scope_for(slots, window)
    return out
