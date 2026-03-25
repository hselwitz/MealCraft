from app.routers.feedback import router as feedback_router
from app.routers.grocery import router as grocery_router
from app.routers.leftovers import router as leftovers_router
from app.routers.plans import router as plans_router
from app.routers.recipes import router as recipes_router
from app.routers.settings import router as settings_router

__all__ = [
    "plans_router",
    "recipes_router",
    "leftovers_router",
    "grocery_router",
    "feedback_router",
    "settings_router",
]
