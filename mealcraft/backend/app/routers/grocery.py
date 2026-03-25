"""Grocery router."""

import logging

from app.db import get_db
from app.models.grocery import GroceryList, GroceryItem
from app.models.ingredient import Ingredient
from app.schemas.grocery import GroceryListOut, GroceryItemUpdate
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/grocery-lists", tags=["grocery"])
logger = logging.getLogger(__name__)


async def _load_grocery_list(list_id: str, db: AsyncSession) -> GroceryList:
    result = await db.execute(
        select(GroceryList)
        .where(GroceryList.id == list_id)
        .options(selectinload(GroceryList.items).selectinload(GroceryItem.ingredient))
    )
    gl = result.scalar_one_or_none()
    if not gl:
        raise HTTPException(status_code=404, detail="Grocery list not found")
    return gl


def _grocery_list_to_out(gl: GroceryList) -> dict:
    return {
        "id": gl.id,
        "meal_plan_id": gl.meal_plan_id,
        "generated_at": gl.generated_at.isoformat(),
        "status": gl.status,
        "items": [
            {
                "id": item.id,
                "grocery_list_id": item.grocery_list_id,
                "ingredient_id": item.ingredient_id,
                "ingredient_name": item.ingredient.canonical_name if item.ingredient else "",
                "quantity": float(item.quantity),
                "unit": item.unit,
                "store_section": item.store_section,
                "checked": item.checked,
            }
            for item in sorted(gl.items, key=lambda x: x.store_section)
        ],
    }


@router.get("/{list_id}")
async def get_grocery_list(list_id: str, db: AsyncSession = Depends(get_db)):
    gl = await _load_grocery_list(list_id, db)
    return _grocery_list_to_out(gl)


@router.patch("/{list_id}/items/{item_id}")
async def update_grocery_item(
    list_id: str,
    item_id: str,
    body: GroceryItemUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GroceryItem)
        .where(GroceryItem.id == item_id, GroceryItem.grocery_list_id == list_id)
        .options(selectinload(GroceryItem.ingredient))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Grocery item not found")

    if body.checked is not None:
        item.checked = body.checked
    if body.quantity is not None:
        item.quantity = body.quantity
    if body.unit is not None:
        item.unit = body.unit

    db.add(item)
    await db.flush()

    return {
        "id": item.id,
        "grocery_list_id": item.grocery_list_id,
        "ingredient_id": item.ingredient_id,
        "ingredient_name": item.ingredient.canonical_name if item.ingredient else "",
        "quantity": float(item.quantity),
        "unit": item.unit,
        "store_section": item.store_section,
        "checked": item.checked,
    }
