"""Plans router."""

import json
import logging
from typing import Optional

from app.db import get_db
from app.llm.client import get_llm_client, LLMClient
from app.models.grocery import GroceryList, GroceryItem
from app.models.ingredient import RecipeIngredient
from app.models.meal_plan import MealPlan, MealSlot
from app.models.prep_plan import PrepPlanRecord
from app.models.recipe import Recipe, RecipeStep
from app.schemas.plan import (
    MealPlanCreate,
    MealPlanUpdate,
    MealPlanOut,
    MealSlotOut,
    MealSlotUpdate,
    MealPlanListItem,
    PrepPlanPatch,
    PrepPlanRequest,
)
from app.services.grocery import GroceryService
from app.services.planner import PlannerService
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/plans", tags=["plans"])
logger = logging.getLogger(__name__)


async def _load_plan_with_slots(plan_id: str, db: AsyncSession) -> MealPlan:
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.id == plan_id)
        .options(selectinload(MealPlan.slots).selectinload(MealSlot.recipe))
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("", response_model=MealPlanOut, status_code=201)
async def create_plan(
    body: MealPlanCreate,
    db: AsyncSession = Depends(get_db),
):
    plan = MealPlan(
        name=body.name,
        start_date=body.start_date,
        end_date=body.end_date,
        calorie_target=body.calorie_target,
        status="draft",
    )
    db.add(plan)
    await db.flush()

    for slot_cfg in body.slots_config:
        slot = MealSlot(
            meal_plan_id=plan.id,
            date=slot_cfg.date,
            meal_type=slot_cfg.meal_type,
            status=slot_cfg.status,
            servings=2.0,
        )
        db.add(slot)

    await db.flush()
    return await _load_plan_with_slots(plan.id, db)


@router.get("", response_model=list[MealPlanListItem])
async def list_plans(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(MealPlan).order_by(desc(MealPlan.created_at)).limit(limit)
    if cursor:
        # cursor is a plan id; get its created_at for comparison
        cursor_result = await db.execute(select(MealPlan).where(MealPlan.id == cursor))
        cursor_plan = cursor_result.scalar_one_or_none()
        if cursor_plan:
            query = query.where(MealPlan.created_at < cursor_plan.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{plan_id}", response_model=MealPlanOut)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    return await _load_plan_with_slots(plan_id, db)


@router.patch("/{plan_id}", response_model=MealPlanOut)
async def update_plan(
    plan_id: str,
    body: MealPlanUpdate,
    db: AsyncSession = Depends(get_db),
):
    plan = await _load_plan_with_slots(plan_id, db)
    if body.name is not None:
        plan.name = body.name
    if body.status is not None:
        plan.status = body.status
    if body.calorie_target is not None:
        plan.calorie_target = body.calorie_target
    db.add(plan)
    await db.flush()
    return await _load_plan_with_slots(plan_id, db)


@router.put("/{plan_id}/slots/{slot_id}", response_model=MealSlotOut)
async def update_slot(
    plan_id: str,
    slot_id: str,
    body: MealSlotUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MealSlot)
        .where(MealSlot.id == slot_id, MealSlot.meal_plan_id == plan_id)
        .options(selectinload(MealSlot.recipe))
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if body.status is not None:
        slot.status = body.status
    if body.recipe_id is not None:
        slot.recipe_id = body.recipe_id
    if body.servings is not None:
        slot.servings = body.servings
    if body.notes is not None:
        slot.notes = body.notes

    db.add(slot)
    await db.flush()

    # Reload with recipe
    result = await db.execute(
        select(MealSlot).where(MealSlot.id == slot_id).options(selectinload(MealSlot.recipe))
    )
    return result.scalar_one()


@router.post("/{plan_id}/slots/{slot_id}/regenerate", response_model=MealSlotOut)
async def regenerate_slot(
    plan_id: str,
    slot_id: str,
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    result = await db.execute(
        select(MealSlot)
        .where(MealSlot.id == slot_id, MealSlot.meal_plan_id == plan_id)
        .options(selectinload(MealSlot.recipe))
    )
    slot = result.scalar_one_or_none()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    plan_result = await db.execute(select(MealPlan).where(MealPlan.id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    planner = PlannerService(db, llm)
    recipe = await planner.regenerate_slot_recipe(slot, plan, {})

    result = await db.execute(
        select(MealSlot).where(MealSlot.id == slot_id).options(selectinload(MealSlot.recipe))
    )
    return result.scalar_one()


@router.post("/{plan_id}/generate")
async def generate_plan(
    plan_id: str,
    request: Request,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    plan = await _load_plan_with_slots(plan_id, db)
    planner = PlannerService(db, llm)
    preferences = body.get("preferences", {})

    async def event_stream():
        try:
            async for msg in planner.generate_plan(
                plan=plan,
                preferences=preferences,
                schedule=body.get("schedule", {}),
                leftovers=body.get("leftovers", []),
                pantry=body.get("pantry", []),
            ):
                if msg == "__DONE__":
                    yield f"data: {json.dumps({'status': 'complete', 'plan_id': plan_id})}\n\n"
                else:
                    yield f"data: {json.dumps({'message': msg})}\n\n"
        except Exception as e:
            logger.exception("Plan generation failed")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/{plan_id}/prep-plan")
async def generate_prep_plan(
    plan_id: str,
    body: PrepPlanRequest,
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    plan = await _load_plan_with_slots(plan_id, db)

    recipes_data = []
    for slot in plan.slots:
        if slot.recipe and slot.status == "planned":
            recipe = slot.recipe
            ri_result = await db.execute(
                select(RecipeIngredient)
                .where(RecipeIngredient.recipe_id == recipe.id)
                .options(selectinload(RecipeIngredient.ingredient))
            )
            recipe_ingredients = ri_result.scalars().all()

            steps_result = await db.execute(
                select(RecipeStep)
                .where(RecipeStep.recipe_id == recipe.id)
                .order_by(RecipeStep.step_number)
            )
            steps = steps_result.scalars().all()

            recipes_data.append(
                {
                    "title": recipe.title,
                    "servings": float(recipe.servings),
                    "prep_time_min": recipe.prep_time_min,
                    "cook_time_min": recipe.cook_time_min,
                    "scheduled_date": str(slot.date),
                    "meal_type": slot.meal_type,
                    "ingredients": [
                        {
                            "ingredient_name": ri.ingredient.canonical_name,
                            "quantity": float(ri.quantity),
                            "unit": ri.unit,
                            "prep_note": ri.prep_note,
                        }
                        for ri in recipe_ingredients
                    ],
                    "steps": [
                        {
                            "step_number": s.step_number,
                            "instruction": s.instruction,
                            "duration_min": s.duration_min,
                            "is_active": s.is_active,
                        }
                        for s in steps
                    ],
                }
            )

    if not recipes_data:
        raise HTTPException(status_code=400, detail="No recipes found for this plan")

    prep_plan = await llm.optimize_prep_plan(recipes_data, body.time_windows)

    # Persist — replace any existing prep plan for this plan
    existing = await db.execute(
        select(PrepPlanRecord).where(PrepPlanRecord.meal_plan_id == plan_id)
    )
    for old in existing.scalars().all():
        await db.delete(old)

    data = prep_plan.model_dump()
    data["completed_tasks"] = []
    record = PrepPlanRecord(meal_plan_id=plan_id, data=data)
    db.add(record)
    await db.flush()

    return data


@router.get("/{plan_id}/prep-plan/current")
async def get_current_prep_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrepPlanRecord)
        .where(PrepPlanRecord.meal_plan_id == plan_id)
        .order_by(desc(PrepPlanRecord.created_at))
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="No prep plan found for this plan")
    return record.data


@router.patch("/{plan_id}/prep-plan/current")
async def patch_current_prep_plan(
    plan_id: str,
    body: PrepPlanPatch,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PrepPlanRecord)
        .where(PrepPlanRecord.meal_plan_id == plan_id)
        .order_by(desc(PrepPlanRecord.created_at))
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="No prep plan found for this plan")
    updated = dict(record.data)
    updated["completed_tasks"] = body.completed_tasks
    record.data = updated
    await db.flush()
    return record.data


@router.get("/{plan_id}/grocery-list/current")
async def get_current_grocery_list(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroceryList)
        .where(GroceryList.meal_plan_id == plan_id)
        .order_by(desc(GroceryList.generated_at))
        .limit(1)
    )
    grocery_list = result.scalar_one_or_none()
    if not grocery_list:
        raise HTTPException(status_code=404, detail="No grocery list found for this plan")

    items_result = await db.execute(
        select(GroceryItem)
        .where(GroceryItem.grocery_list_id == grocery_list.id)
        .options(selectinload(GroceryItem.ingredient))
    )
    items = items_result.scalars().all()

    return {
        "id": grocery_list.id,
        "meal_plan_id": grocery_list.meal_plan_id,
        "items": [
            {
                "id": item.id,
                "ingredient_name": item.ingredient.canonical_name if item.ingredient else "",
                "quantity": float(item.quantity),
                "unit": item.unit,
                "store_section": item.store_section,
                "checked": item.checked,
            }
            for item in items
        ],
    }


@router.post("/{plan_id}/grocery-list")
async def generate_grocery_list(
    plan_id: str,
    body: dict = {},
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    plan_result = await db.execute(select(MealPlan).where(MealPlan.id == plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    pantry_staples = body.get("pantry_staples") or None
    grocery_svc = GroceryService(db, llm)
    grocery_list = await grocery_svc.generate_for_plan(plan_id, pantry_staples=pantry_staples)

    return {"grocery_list_id": grocery_list.id, "status": "generated"}
