from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):

    APP_NAME: str
    APP_ENV: str

    SECRET_KEY: str
    ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int

    DATABASE_URL: str

    LOG_DIR: str = "logs"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5
    SQLALCHEMY_LOG_LEVEL: str = "WARNING"

    CORS_ORIGINS: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,"
        "http://localhost:3000,http://100.93.158.60:3000/,http://100.75.166.124:3000/"

    )
    APP_TAGLINE: str = "Extrusion Production Intelligence"
    OPERATOR_ASSIST_URL: str = "http://sunpor-operator-assist:8010"
    OPERATOR_ASSIST_TIMEOUT_SECONDS: float = 3.0
    # Single switch for UI + shift wall-clock: austria | pakistan | usa
    DISPLAY_TIMEZONE_REGION: str = "austria"
    # Deprecated: use DISPLAY_TIMEZONE_REGION (kept for backward-compatible .env)
    PLANT_TIMEZONE: str | None = None

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()