import logging
import logging.config
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _resolve_log_dir() -> Path:
    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _build_handlers(log_dir: Path) -> dict:
    max_bytes = int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    return {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
            "level": "DEBUG",
        },
        "app_file": {
            "()": RotatingFileHandler,
            "formatter": "default",
            "filename": str(log_dir / "backend.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "level": "DEBUG",
        },
        "error_file": {
            "()": RotatingFileHandler,
            "formatter": "default",
            "filename": str(log_dir / "backend.error.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "level": "ERROR",
        },
        "access_file": {
            "()": RotatingFileHandler,
            "formatter": "access",
            "filename": str(log_dir / "access.log"),
            "maxBytes": max_bytes,
            "backupCount": backup_count,
            "encoding": "utf-8",
            "level": "INFO",
        },
    }


def setup_logging(log_level: str | None = None) -> None:
    level_name = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    log_dir = _resolve_log_dir()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "access": {
                "format": "%(asctime)s | %(levelname)-8s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": _build_handlers(log_dir),
        "root": {
            "level": level,
            "handlers": ["console", "app_file", "error_file"],
        },
        "loggers": {
            "app": {
                "level": level,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "uvicorn": {
                "level": level,
                "handlers": ["console", "app_file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": level,
                "handlers": ["console", "app_file", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "access_file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": os.getenv("SQLALCHEMY_LOG_LEVEL", "WARNING").upper(),
                "handlers": ["console", "app_file"],
                "propagate": False,
            },
            "alembic": {
                "level": "INFO",
                "handlers": ["console", "app_file"],
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)

    logger = logging.getLogger("app.logging")
    logger.info(
        "Logging initialized | level=%s | log_dir=%s",
        level_name,
        log_dir.resolve(),
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")
