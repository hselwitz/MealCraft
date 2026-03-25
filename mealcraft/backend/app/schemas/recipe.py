from typing import Optional, List

from pydantic import BaseModel, Field


class RecipeStepOut(BaseModel):
    id: str
    step_number: int
    instruction: str
    duration_min: Optional[int] = None
    is_active: bool

    model_config = {"from_attributes": True}


class RecipeIngredientOut(BaseModel):
    id: str
    ingredient_id: str
    ingredient_name: str
    quantity: float
    unit: str
    prep_note: Optional[str] = None
    is_optional: bool

    model_config = {"from_attributes": True}


class RecipeOut(BaseModel):
    id: str
    title: str
    description: str
    prep_time_min: int
    cook_time_min: int
    total_time_min: int
    difficulty: str
    servings: float
    calories_per_serving: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    tags: list = Field(default_factory=list)
    steps: List[RecipeStepOut] = Field(default_factory=list)
    recipe_ingredients: List[RecipeIngredientOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RecipeListItem(BaseModel):
    id: str
    title: str
    description: str
    prep_time_min: int
    cook_time_min: int
    difficulty: str
    servings: float
    calories_per_serving: Optional[int] = None
    tags: list = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RecipeGenerateRequest(BaseModel):
    concept: str
    dietary_restrictions: List[str] = Field(default_factory=list)
    max_difficulty: str = "medium"
    target_servings: float = 4.0
