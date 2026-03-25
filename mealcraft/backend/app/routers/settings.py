"""Settings router — single-user app settings persisted in DB."""

from datetime import datetime, timezone

from app.db import get_db
from app.models.settings import AppSettings
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "maxDifficulty": "medium",
    "ingredientOverlap": "medium",
    "defaultServings": 2,
    "calorieTarget": 2500,
    "cuisinePreferences": [],
    "dietaryRestrictions": [],
    "pantryStaples": [
        "salt", "black pepper", "olive oil", "vegetable oil",
        "sugar", "all-purpose flour", "baking soda", "baking powder",
    ],
}

SETTINGS_ID = "default"


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
    row = result.scalar_one_or_none()
    if not row:
        return DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS, **row.data}


@router.put("")
async def update_settings(body: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
    row = result.scalar_one_or_none()
    if row:
        row.data = body
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = AppSettings(id=SETTINGS_ID, data=body)
        db.add(row)
    await db.flush()
    return {**DEFAULT_SETTINGS, **row.data}
