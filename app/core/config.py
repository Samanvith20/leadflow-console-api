from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Leadflow API"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = (
        "postgresql+psycopg://leadflow:leadflow_dev_password@localhost:5432/leadflow"
    )
    session_lifetime_days: int = 7
    session_cookie_name: str = "leadflow_session"
    session_cookie_secure: bool = False
    password_reset_lifetime_minutes: int = 30
    email_verification_lifetime_hours: int = 24
    frontend_base_url: str = "http://localhost:3000"
    resend_api_key: str | None = None
    email_from: str | None = None
    webhook_encryption_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def require_email_delivery_in_production(self) -> "Settings":
        """Prevent a production API from silently creating undeliverable auth links."""
        if self.environment.lower() == "production" and (
            not self.resend_api_key or not self.email_from
        ):
            raise ValueError("RESEND_API_KEY and EMAIL_FROM are required in production")
        if self.environment.lower() == "production" and not self.session_cookie_secure:
            raise ValueError("SESSION_COOKIE_SECURE must be true in production")
        if self.environment.lower() == "production" and not self.webhook_encryption_key:
            raise ValueError("WEBHOOK_ENCRYPTION_KEY is required in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
