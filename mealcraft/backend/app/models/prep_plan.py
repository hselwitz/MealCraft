import uuid
from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import VARCHAR, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PrepPlanRecord(Base):
    __tablename__ = "prep_plans"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True, default=_uuid)
    meal_plan_id: Mapped[str] = mapped_column(
        VARCHAR(36), ForeignKey("meal_plans.id"), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)
