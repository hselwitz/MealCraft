from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(settings.database_url, echo=False, future=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables on startup."""
    from app.models import meal_plan, recipe, ingredient, leftover, grocery  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from app.models.repertoire import RepertoireMeal, FAMILIAR_MEALS
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        # Fresh installs receive the three familiar meals; existing entries are preserved.
        for meal in FAMILIAR_MEALS:
            exists = await session.scalar(select(RepertoireMeal.id).where(RepertoireMeal.id == meal["id"]))
            if not exists:
                session.add(RepertoireMeal(**meal, familiar=True, saved=True))
        await session.commit()
