from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class GroceryItemOut(BaseModel):
    id: str
    grocery_list_id: str
    ingredient_id: str
    ingredient_name: str
    quantity: float
    unit: str
    store_section: str
    checked: bool

    model_config = {"from_attributes": True}


class GroceryItemUpdate(BaseModel):
    checked: Optional[bool] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None


class GroceryListOut(BaseModel):
    id: str
    meal_plan_id: str
    generated_at: datetime
    status: str
    items: List[GroceryItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}
