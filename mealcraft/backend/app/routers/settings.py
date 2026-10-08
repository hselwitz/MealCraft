"""Settings router — single-user app settings persisted in DB."""

from datetime import datetime, timezone

from app.db import get_db
from app.models.settings import AppSettings
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/settings", tags=["settings"])

DEFAULT_SETTINGS = {
    "openRouterModel": settings.openrouter_model,
    "maxDifficulty": "medium",
    "ingredientOverlap": "medium",
    "defaultServings": 2,
    "calorieTarget": 2500,
    "cuisinePreferences": [],
    "dietaryRestrictions": [],
    "pantryStaples": [
        "salt",
        "black pepper",
        "olive oil",
        "vegetable oil",
        "sugar",
        "all-purpose flour",
        "baking soda",
        "baking powder",
    ],
}

SETTINGS_ID = "default"


def public_settings(data: dict) -> dict:
    public = {**DEFAULT_SETTINGS, **data}
    key = public.pop("openRouterApiKey", "")
    public["hasOpenRouterKey"] = bool(key or settings.openrouter_api_key)
    public["openRouterKeySource"] = "settings" if key else "environment" if settings.openrouter_api_key else None
    return public


@router.get("")
async def get_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
    row = result.scalar_one_or_none()
    return public_settings(row.data if row else {})


@router.put("")
async def update_settings(body: dict, db: AsyncSession = Depends(get_db)):
    updates = {k: v for k, v in body.items()
               if k not in {"hasOpenRouterKey", "openRouterKeySource"}}
    if "openRouterApiKey" in updates:
        key = updates["openRouterApiKey"]
        if key is not None and not isinstance(key, str):
            raise HTTPException(status_code=422, detail="OpenRouter key must be text.")
        # Null explicitly removes the saved key; blank text leaves it unchanged.
        if key is None:
            updates["openRouterApiKey"] = ""
        elif not key.strip():
            updates.pop("openRouterApiKey")
        else:
            updates["openRouterApiKey"] = key.strip()
    if "openRouterModel" in updates:
        model = updates["openRouterModel"]
        if not isinstance(model, str) or not model.strip() or "/" not in model.strip():
            raise HTTPException(status_code=422, detail="Use an OpenRouter model ID such as anthropic/claude-sonnet-4.")
        updates["openRouterModel"] = model.strip()
    result = await db.execute(select(AppSettings).where(AppSettings.id == SETTINGS_ID))
    row = result.scalar_one_or_none()
    if row:
        row.data = {**row.data, **updates}
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = AppSettings(id=SETTINGS_ID, data=updates)
        db.add(row)
    await db.flush()
    return public_settings(row.data)
