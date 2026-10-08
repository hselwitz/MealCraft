from typing import Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, model_validator


class DiscoveryRequest(BaseModel):
    request: str = Field(default="", max_length=2000)
    direction: Literal["usual", "twist", "new"] = "twist"
    max_active_min: int = Field(default=15, ge=5, le=60)
    familiar_meal_id: str | None = None
    planning_start_date: date | None = None
    planning_end_date: date | None = None
    avoid_titles: list[str] = Field(default_factory=list, max_length=12)


class DinnerIdea(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=700)
    familiar_connection: str = Field(max_length=400)
    active_time_min: int = Field(ge=1, le=60)
    total_time_min: int = Field(ge=1, le=240)
    cleanup: str = Field(min_length=1, max_length=200)
    extra_ingredients: list[str] = Field(max_length=3)
    convenience_tip: str = Field(min_length=1, max_length=400)

    @model_validator(mode="after")
    def elapsed_covers_active(self):
        if self.total_time_min < self.active_time_min:
            raise ValueError("Elapsed time cannot be shorter than hands-on time.")
        return self


class DinnerIdeas(BaseModel):
    ideas: list[DinnerIdea] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def distinct_titles(self):
        if len({idea.title.strip().casefold() for idea in self.ideas}) != 3:
            raise ValueError("Dinner ideas must have three distinct titles. Please try again.")
        return self


class DinnerRecipeRequest(BaseModel):
    idea: DinnerIdea
    max_active_min: int = Field(default=15, ge=5, le=60)
    request: str = Field(default="", max_length=2000)


class RepertoireOut(BaseModel):
    id: str
    recipe_id: str | None
    title: str
    notes: str
    familiar: bool
    saved: bool
    verdict: str | None
    easy_enough: bool | None
    cooked_count: int
    last_cooked_at: datetime | None
    model_config = {"from_attributes": True}


class RepertoireCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str = Field(default="", max_length=2000)


class RepertoireUpdate(BaseModel):
    saved: bool | None = None
    cooked: bool = False
    verdict: Literal["again", "adjust", "no"] | None = None
    easy_enough: bool | None = None
    notes: str | None = Field(default=None, max_length=2000)
