from datetime import datetime, timezone

from app.db import Base
from sqlalchemy import VARCHAR, JSON, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(timezone.utc)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id: Mapped[str] = mapped_column(VARCHAR(36), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=_now)
