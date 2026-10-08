"""Personal meals, saved recipes, and lightweight cooking feedback."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

FAMILIAR_MEALS = [
    {"id": "usual-chicken", "title": "Chili chicken with rice or quinoa", "notes": "Skin-on, bone-in chicken breast with white rice or quinoa and chili paste. Frozen bell peppers and onions when available."},
    {"id": "usual-pasta", "title": "Wheat pasta with chicken or beef", "notes": "Wheat pasta, olive oil, marinara, and chicken or ground beef."},
    {"id": "usual-beef", "title": "Beef patties, potato & sauerkraut", "notes": "Ground beef patties, a microwaved baked potato, and sauerkraut."},
]


class RepertoireMeal(Base):
    __tablename__ = "repertoire_meals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recipe_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("recipes.id", ondelete="CASCADE"), unique=True)
    title: Mapped[str] = mapped_column(String(255))
    notes: Mapped[str] = mapped_column(Text, default="")
    familiar: Mapped[bool] = mapped_column(Boolean, default=False)
    saved: Mapped[bool] = mapped_column(Boolean, default=True)
    verdict: Mapped[str | None] = mapped_column(String(20))
    easy_enough: Mapped[bool | None] = mapped_column(Boolean)
    cooked_count: Mapped[int] = mapped_column(Integer, default=0)
    last_cooked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
