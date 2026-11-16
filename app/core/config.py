from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Leadflow API"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = (
        "postgresql+psycopg://leadflow:leadflow_dev_password@localhost:5432/leadflow"
    )
    session_lifetime_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
