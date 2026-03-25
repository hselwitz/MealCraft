from typing import Optional

from pydantic import BaseModel


class LeftoverCreate(BaseModel):
    meal_slot_id: str
    recipe_id: str
    remaining_servings: float
    stored_date: str
    expiry_date: Optional[str] = None


class LeftoverUpdate(BaseModel):
    status: Optional[str] = None
    remaining_servings: Optional[float] = None
    used_in_slot_id: Optional[str] = None


class RecipeSummary(BaseModel):
    id: str
    title: str

    model_config = {"from_attributes": True}


class LeftoverOut(BaseModel):
    id: str
    meal_slot_id: str
    recipe_id: str
    remaining_servings: float
    stored_date: str
    expiry_date: str
    status: str
    used_in_slot_id: Optional[str] = None
    recipe: Optional[RecipeSummary] = None

    model_config = {"from_attributes": True}


class LeftoverSuggestionRequest(BaseModel):
    empty_slots: list = []
