"""Leftovers router."""

import logging
from typing import Optional

from app.db import get_db
from app.llm.client import get_llm_client, LLMClient
from app.models.leftover import Leftover
from app.models.recipe import Recipe
from app.schemas.leftover import (
    LeftoverCreate,
    LeftoverOut,
    LeftoverUpdate,
    LeftoverSuggestionRequest,
)
from app.services.leftover import LeftoverService
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/leftovers", tags=["leftovers"])
logger = logging.getLogger(__name__)


async def _load_leftover(leftover_id: str, db: AsyncSession) -> Leftover:
    result = await db.execute(
        select(Leftover).where(Leftover.id == leftover_id).options(selectinload(Leftover.recipe))
    )
    lv = result.scalar_one_or_none()
    if not lv:
        raise HTTPException(status_code=404, detail="Leftover not found")
    return lv


@router.get("", response_model=list[LeftoverOut])
async def list_leftovers(
    status: Optional[str] = Query("available"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Leftover).options(selectinload(Leftover.recipe)).order_by(Leftover.expiry_date)
    if status:
        query = query.where(Leftover.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=LeftoverOut, status_code=201)
async def create_leftover(
    body: LeftoverCreate,
    db: AsyncSession = Depends(get_db),
):
    svc = LeftoverService(db)

    expiry_date = body.expiry_date
    if not expiry_date:
        expiry_date = await svc.estimate_expiry(body.stored_date, body.recipe_id)

    lv = Leftover(
        meal_slot_id=body.meal_slot_id,
        recipe_id=body.recipe_id,
        remaining_servings=body.remaining_servings,
        stored_date=body.stored_date,
        expiry_date=expiry_date,
        status="available",
    )
    db.add(lv)
    await db.flush()
    return await _load_leftover(lv.id, db)


@router.patch("/{leftover_id}", response_model=LeftoverOut)
async def update_leftover(
    leftover_id: str,
    body: LeftoverUpdate,
    db: AsyncSession = Depends(get_db),
):
    lv = await _load_leftover(leftover_id, db)

    if body.status is not None:
        lv.status = body.status
    if body.remaining_servings is not None:
        lv.remaining_servings = body.remaining_servings
    if body.used_in_slot_id is not None:
        lv.used_in_slot_id = body.used_in_slot_id

    db.add(lv)
    await db.flush()
    return await _load_leftover(leftover_id, db)


@router.post("/suggestions")
async def get_suggestions(
    body: LeftoverSuggestionRequest,
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    # Get available leftovers
    result = await db.execute(
        select(Leftover)
        .where(Leftover.status == "available")
        .options(selectinload(Leftover.recipe))
        .order_by(Leftover.expiry_date)
    )
    leftovers = result.scalars().all()

    if not leftovers:
        return {"suggestions": ["No leftovers available to suggest uses for."]}

    leftovers_data = [
        {
            "recipe_title": lv.recipe.title if lv.recipe else "Unknown dish",
            "remaining_servings": float(lv.remaining_servings),
            "expiry_date": str(lv.expiry_date),
            "stored_date": str(lv.stored_date),
        }
        for lv in leftovers
    ]

    suggestions = await llm.suggest_leftover_use(leftovers_data, body.empty_slots)
    return suggestions.model_dump()
