"""Settings and YAML loader for productionController."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml
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
    PC_EMAIL: str
    PC_PASSWORD: str
    CONFIG_PATH: str = "production_config.yaml"

    # Optional ID overrides — skip API resolution if set
    COMPANY_ID: Optional[int] = None
    PRODUCTION_LINE_ID: Optional[int] = None
    OPERATOR_ID: Optional[int] = None
    DEFAULT_MATERIAL_TYPE_ID: Optional[int] = None

    @property
    def backend_base(self) -> str:
        return self.BACKEND_URL.rstrip("/")


def load_pc_config(path: str | Path) -> dict:
    """Load production_config.yaml (same pattern as AI_ML_Service)."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache
def get_settings() -> Settings:
    return Settings()
