from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str = "sqlite+aiosqlite:///./data/mealcraft.db"
    calorie_target: int = 2500
    max_difficulty: str = "medium"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
