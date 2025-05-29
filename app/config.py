from functools import lru_cache
from typing import Optional

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings as PydanticBaseSettings


class Settings(PydanticBaseSettings):
    # Application
    app_name: str = "Chess API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Base de données
    database_url: str
    postgres_db: str
    postgres_user: str
    postgres_password: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Redis (optionnel)
    redis_url: Optional[str] = None

    # CORS
    allowed_origins: list = ["http://localhost:5173", "http://localhost:8080"]

    # Validation
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v

    # Debug mode calculé automatiquement
    @computed_field
    @property
    def debug(self) -> bool:
        return self.environment == "development"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """
    Cache des settings pour éviter de relire le .env à chaque fois
    """
    return Settings()


# Instance globale
settings = get_settings()
