from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "TC Generator"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/tc_generator"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # dtgpt (OpenAI compatible)
    DTGPT_BASE_URL: str = "https://dtgpt.example.com/v1"
    DTGPT_API_KEY: str = ""
    DTGPT_MODEL: str = "dtgpt"

    # Test Executor
    EXECUTOR_BASE_URL: str = "http://localhost:8001"
    EXECUTOR_CALLBACK_URL: str = "http://localhost:8000/api/execution-result"

    # SAML
    SAML_SP_ENTITY_ID: str = "tc-generator"
    SAML_ACS_URL: str = "http://localhost:8000/api/auth/saml/acs"
    SAML_SLO_URL: str = "http://localhost:8000/api/auth/saml/slo"
    SAML_IDP_METADATA_URL: str = ""
    SAML_SETTINGS_PATH: str = "app/core/saml"

    # JWT (for service-to-service)
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
