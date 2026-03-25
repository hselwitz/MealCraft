from typing import Optional, Literal

from pydantic import BaseModel


class RecipeStepOutput(BaseModel):
    step_number: int
    instruction: str
    duration_min: Optional[int] = None
    is_active: bool


class RecipeIngredientOutput(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    prep_note: Optional[str] = None
    is_optional: bool = False


class RecipeOutput(BaseModel):
    title: str
    description: str
    prep_time_min: int
    cook_time_min: int
    total_time_min: int
    difficulty: Literal["easy", "medium", "hard"]
    servings: float
    calories_per_serving: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    tags: list[str] = []
    ingredients: list[RecipeIngredientOutput] = []
    steps: list[RecipeStepOutput] = []


class MealSlotPlan(BaseModel):
    date: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"]
    meal_concept: str
    estimated_prep_min: int
    estimated_cook_min: int
    batch_component: Optional[str] = None


class WeeklyPlanOutput(BaseModel):
    meal_slots: list[MealSlotPlan]
    batch_components: list[str] = []
    estimated_total_active_min: int
    notes: str


class PrepTaskOutput(BaseModel):
    task_name: str
    duration_min: int
    is_active: bool
    batch_group: Optional[str] = None
    depends_on: list[str] = []


class PrepPlanOutput(BaseModel):
    tasks: list[PrepTaskOutput]
    total_active_min: int
    total_passive_min: int
    recommended_sessions: list[str] = []


class GroceryItemOutput(BaseModel):
    ingredient_name: str
    quantity: float
    unit: str
    store_section: Literal["produce", "meat", "dairy", "bakery", "pantry", "frozen", "other"]
    notes: Optional[str] = None


class GroceryListOutput(BaseModel):
    items: list[GroceryItemOutput]


class LeftoverSuggestionOutput(BaseModel):
    suggestions: list[str]
