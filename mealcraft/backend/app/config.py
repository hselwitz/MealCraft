from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4"
    database_url: str = "sqlite+aiosqlite:///./data/mealcraft.db"
    calorie_target: int = 2500
    max_difficulty: str = "medium"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
