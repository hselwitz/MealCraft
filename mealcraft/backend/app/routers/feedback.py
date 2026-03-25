"""Feedback router."""
import logging
from collections import Counter
from typing import Optional

from app.db import get_db
from app.models.meal_plan import MealFeedback
from app.schemas.plan import FeedbackCreate, FeedbackOut
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


@router.post("", response_model=FeedbackOut, status_code=201)
async def submit_feedback(
    body: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
):
    fb = MealFeedback(
        meal_slot_id=body.meal_slot_id,
        recipe_id=body.recipe_id,
        rating=body.rating,
        tags=body.tags,
        note=body.note,
    )
    db.add(fb)
    await db.flush()
    return fb


@router.get("", response_model=list[FeedbackOut])
async def list_feedback(
    cursor: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    recipe_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(MealFeedback).order_by(desc(MealFeedback.created_at)).limit(limit)
    if recipe_id:
        query = query.where(MealFeedback.recipe_id == recipe_id)
    if cursor:
        cursor_result = await db.execute(
            select(MealFeedback).where(MealFeedback.id == cursor)
        )
        cursor_fb = cursor_result.scalar_one_or_none()
        if cursor_fb:
            query = query.where(MealFeedback.created_at < cursor_fb.created_at)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/summary")
async def get_feedback_summary(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MealFeedback))
    all_feedback = result.scalars().all()

    total = len(all_feedback)
    thumbs_up = sum(1 for f in all_feedback if f.rating == "thumbs_up")
    thumbs_down = total - thumbs_up

    # Aggregate tags
    tag_counts: Counter = Counter()
    for fb in all_feedback:
        if fb.tags:
            for tag in (fb.tags if isinstance(fb.tags, list) else []):
                tag_counts[tag] += 1

    # Top rated recipes
    recipe_ratings: dict = {}
    for fb in all_feedback:
        if fb.recipe_id not in recipe_ratings:
            recipe_ratings[fb.recipe_id] = {"up": 0, "down": 0}
        if fb.rating == "thumbs_up":
            recipe_ratings[fb.recipe_id]["up"] += 1
        else:
            recipe_ratings[fb.recipe_id]["down"] += 1

    top_recipes = sorted(
        [
            {"recipe_id": k, "thumbs_up": v["up"], "thumbs_down": v["down"]}
            for k, v in recipe_ratings.items()
        ],
        key=lambda x: x["thumbs_up"] - x["thumbs_down"],
        reverse=True,
    )[:10]

    return {
        "total_feedback": total,
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "approval_rate": round(thumbs_up / total * 100, 1) if total > 0 else 0,
        "top_tags": tag_counts.most_common(10),
        "top_recipes": top_recipes,
    }
