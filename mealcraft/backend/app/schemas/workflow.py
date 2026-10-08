from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator
from app.llm.schemas import PrepPlanOutput, PrepIngredientOutput


class PlanningWindow(BaseModel):
    start_date: date
    end_date: date
    @model_validator(mode="after")
    def ordered(self):
        if self.end_date < self.start_date or (self.end_date-self.start_date).days > 30:
            raise ValueError("Choose an ordered planning window of at most 31 days.")
        return self


class ScheduleRecipe(BaseModel):
    recipe_id: str
    date: date
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "dinner"
    servings: float = Field(ge=0.5, le=24)


class MealFinish(BaseModel):
    recipe_id: str
    title: str
    instructions: str
    active_min: int = Field(ge=0)


class CoordinatedPrep(PrepPlanOutput):
    session_elapsed_min: int = Field(ge=1)
    shared_components: list[str]
    meal_finishes: list[MealFinish]
    grocery_ingredients: list[PrepIngredientOutput]
