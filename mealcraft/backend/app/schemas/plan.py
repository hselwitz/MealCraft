from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field


class SlotConfig(BaseModel):
    date: date
    meal_type: str
    status: str = "planned"


class MealPlanCreate(BaseModel):
    name: str
    start_date: date
    end_date: date
    calorie_target: Optional[int] = 2500
    slots_config: List[SlotConfig] = Field(default_factory=list)


class MealPlanUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    calorie_target: Optional[int] = None


class RecipeSummary(BaseModel):
    id: str
    title: str
    description: str
    prep_time_min: int
    cook_time_min: int
    total_time_min: int
    difficulty: str
    servings: float
    calories_per_serving: Optional[int] = None
    tags: list = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MealSlotOut(BaseModel):
    id: str
    meal_plan_id: str
    date: date
    meal_type: str
    status: str
    recipe_id: Optional[str] = None
    servings: float
    notes: Optional[str] = None
    recipe: Optional[RecipeSummary] = None

    model_config = {"from_attributes": True}


class MealSlotUpdate(BaseModel):
    status: Optional[str] = None
    recipe_id: Optional[str] = None
    servings: Optional[float] = None
    notes: Optional[str] = None


class MealPlanOut(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    calorie_target: Optional[int] = None
    status: str
    created_at: datetime
    slots: List[MealSlotOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MealPlanListItem(BaseModel):
    id: str
    name: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeedbackCreate(BaseModel):
    meal_slot_id: Optional[str] = None
    recipe_id: str
    rating: str
    tags: Optional[list] = None
    note: Optional[str] = None


class FeedbackOut(BaseModel):
    id: str
    meal_slot_id: Optional[str] = None
    recipe_id: str
    rating: str
    tags: Optional[list] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PrepPlanRequest(BaseModel):
    dietary_restrictions: List[str] = []


class PrepPlanPatch(BaseModel):
    completed_tasks: List[str]
