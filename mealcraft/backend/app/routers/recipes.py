"""Recipes router."""

import logging
from typing import Optional

from app.db import get_db
from app.llm.client import get_llm_client, LLMClient
from app.models.ingredient import RecipeIngredient
from app.models.recipe import Recipe, RecipeStep
from app.schemas.recipe import RecipeOut, RecipeListItem, RecipeGenerateRequest, RecipeIngredientOut
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/recipes", tags=["recipes"])
logger = logging.getLogger(__name__)


async def _load_recipe(recipe_id: str, db: AsyncSession) -> Recipe:
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.steps),
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient),
        )
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


def _recipe_to_out(recipe: Recipe) -> dict:
    out = {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "prep_time_min": recipe.prep_time_min,
        "cook_time_min": recipe.cook_time_min,
        "total_time_min": recipe.total_time_min,
        "difficulty": recipe.difficulty,
        "servings": float(recipe.servings),
        "calories_per_serving": recipe.calories_per_serving,
        "protein_g": float(recipe.protein_g) if recipe.protein_g else None,
        "carbs_g": float(recipe.carbs_g) if recipe.carbs_g else None,
        "fat_g": float(recipe.fat_g) if recipe.fat_g else None,
        "tags": recipe.tags or [],
        "steps": [
            {
                "id": s.id,
                "step_number": s.step_number,
                "instruction": s.instruction,
                "duration_min": s.duration_min,
                "is_active": s.is_active,
            }
            for s in sorted(recipe.steps, key=lambda x: x.step_number)
        ],
        "recipe_ingredients": [
            {
                "id": ri.id,
                "ingredient_id": ri.ingredient_id,
                "ingredient_name": ri.ingredient.canonical_name,
                "quantity": float(ri.quantity),
                "unit": ri.unit,
                "prep_note": ri.prep_note,
                "is_optional": ri.is_optional,
            }
            for ri in recipe.recipe_ingredients
        ],
    }
    return out


@router.get("", response_model=list[RecipeListItem])
async def list_recipes(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Recipe).order_by(desc(Recipe.created_at)).limit(limit)
    if cursor:
        cursor_result = await db.execute(select(Recipe).where(Recipe.id == cursor))
        cursor_recipe = cursor_result.scalar_one_or_none()
        if cursor_recipe:
            query = query.where(Recipe.created_at < cursor_recipe.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{recipe_id}")
async def get_recipe(recipe_id: str, db: AsyncSession = Depends(get_db)):
    recipe = await _load_recipe(recipe_id, db)
    return _recipe_to_out(recipe)


@router.post("/generate")
async def generate_recipe(
    body: RecipeGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    """Generate a new recipe. Supports SSE streaming via Accept: text/event-stream."""
    accept = request.headers.get("accept", "")
    constraints = {
        "target_servings": body.target_servings,
        "max_difficulty": body.max_difficulty,
        "dietary_restrictions": body.dietary_restrictions,
    }

    if "text/event-stream" in accept:

        async def _stream():
            async for chunk in llm.generate_recipe_stream(body.concept, constraints):
                yield chunk
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            _stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # Non-streaming: generate and save
    from app.services.planner import PlannerService

    planner = PlannerService(db, llm)
    recipe = await planner._generate_and_save_recipe(body.concept, constraints)

    recipe = await _load_recipe(recipe.id, db)
    return _recipe_to_out(recipe)
