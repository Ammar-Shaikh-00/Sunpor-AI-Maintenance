"""Centralized configuration for the SUNPOR AI_ML_Service.

All values are loaded from the environment (.env). Nothing is hardcoded here:
secrets have no defaults and must be supplied via the environment.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings sourced from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    BACKEND_URL: str
    ML_SERVICE_EMAIL: str
    ML_SERVICE_PASSWORD: str

    ML_SERVICE_PORT: int = 8001
    POLL_INTERVAL_SEC: int = 10
    LOG_LEVEL: str = "INFO"

    STALE_COUNT: int = 5
    WINDOW_SIZE: int = 30
    MIN_SAMPLES: int = 10
    READY_RATIO_THRESHOLD: float = 0.8

    PREDICT_EVERY_N_POLLS: int = 3
    RULES_CONFIG_PATH: str = "state/rules_config.yaml"

    @property
    def backend_base(self) -> str:
        """Backend URL without a trailing slash, safe for path joining."""
        return self.BACKEND_URL.rstrip("/")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (read .env only once)."""
    return Settings()
