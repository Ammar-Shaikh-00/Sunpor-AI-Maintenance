"""UTC helpers for database persistence and display-timezone API responses.

Storage convention: naive UTC in PostgreSQL (``timestamp without time zone``).
Display convention: API JSON datetimes are converted to the configured region
(``DISPLAY_TIMEZONE_REGION``) before reaching the UI.
"""

from __future__ import annotations

import re
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import DateTime as SADateTime
from sqlalchemy import inspect

from app.core.config import settings

logger = logging.getLogger("app.datetime")

# Single switch: change region here or via DISPLAY_TIMEZONE_REGION in .env
DISPLAY_TIMEZONE_REGIONS: dict[str, str] = {
    "austria": "Europe/Vienna",
    "pakistan": "Asia/Karachi",
    "usa": "America/New_York",
}

DEFAULT_DISPLAY_TIMEZONE_REGION = "austria"
FALLBACK_FIXED_OFFSETS: dict[str, timezone] = {
    "austria": timezone(timedelta(hours=1)),
    "pakistan": timezone(timedelta(hours=5)),
    "usa": timezone(timedelta(hours=-5)),
}

_UTC_NAIVE_ISO = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$"
)
_UTC_ZULU_ISO = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$"
)
_UTC_ZERO_OFFSET_ISO = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?\+00:00$"
)


def get_display_timezone_region() -> str:
    region = (settings.DISPLAY_TIMEZONE_REGION or DEFAULT_DISPLAY_TIMEZONE_REGION).lower().strip()
    if region not in DISPLAY_TIMEZONE_REGIONS:
        return DEFAULT_DISPLAY_TIMEZONE_REGION
    return region


def get_display_timezone() -> ZoneInfo:
    region = get_display_timezone_region()
    tz_name = DISPLAY_TIMEZONE_REGIONS[region]
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        fallback = FALLBACK_FIXED_OFFSETS[region]
        logger.error(
            "ZoneInfo '%s' not found; using fixed-offset fallback. "
            "Install tzdata for DST-aware timezone conversion.",
            tz_name,
        )
        return fallback


def get_display_timezone_label() -> str:
    return DISPLAY_TIMEZONE_REGIONS[get_display_timezone_region()]


def utc_now_naive() -> datetime:
    """Current UTC time as naive datetime (DB convention)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def as_naive_utc(value: datetime | None) -> datetime | None:
    """Convert any datetime to naive UTC for storage."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def utc_naive_to_display(value: datetime | None) -> datetime | None:
    """Convert stored naive UTC to timezone-aware display datetime."""
    if value is None:
        return None
    utc_aware = value.replace(tzinfo=timezone.utc)
    return utc_aware.astimezone(get_display_timezone())


def serialize_datetime_for_display(value: datetime | None) -> str | None:
    """Serialize a stored UTC datetime for API/UI (ISO with display offset)."""
    if value is None:
        return None
    display_dt = utc_naive_to_display(as_naive_utc(value))
    if display_dt is None:
        return None
    return display_dt.isoformat(timespec="seconds")


def parse_stored_utc_string(value: str) -> datetime | None:
    """Parse API/DB UTC strings that still need display conversion."""
    if _UTC_NAIVE_ISO.match(value):
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    if _UTC_ZULU_ISO.match(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    if _UTC_ZERO_OFFSET_ISO.match(value):
        return datetime.fromisoformat(value)
    return None


def convert_datetimes_for_api_response(value: Any) -> Any:
    """Recursively convert UTC datetime strings in JSON responses."""
    if isinstance(value, dict):
        return {
            key: convert_datetimes_for_api_response(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [convert_datetimes_for_api_response(item) for item in value]
    if isinstance(value, str):
        parsed = parse_stored_utc_string(value)
        if parsed is not None:
            return serialize_datetime_for_display(parsed.replace(tzinfo=None))
    return value


def plant_now_naive() -> datetime:
    """Current plant-local wall clock as naive datetime (shift logic only)."""
    return datetime.now(get_display_timezone()).replace(tzinfo=None)


def normalize_datetimes_in_mapping(
    data: dict,
    model_class,
) -> dict:
    """Normalize datetime fields in a create/update payload dict."""
    datetime_fields = _datetime_column_keys(model_class)
    if not datetime_fields:
        return data

    normalized = dict(data)
    for key in datetime_fields:
        if key in normalized and normalized[key] is not None:
            normalized[key] = as_naive_utc(normalized[key])
    return normalized


def normalize_datetime_fields_on_instance(instance) -> None:
    """Normalize all DateTime columns on a SQLAlchemy model instance in place."""
    for key in _datetime_column_keys(instance.__class__):
        value = getattr(instance, key, None)
        if value is not None:
            setattr(instance, key, as_naive_utc(value))


def _datetime_column_keys(model_class) -> set[str]:
    mapper = inspect(model_class)
    keys: set[str] = set()
    for attr in mapper.column_attrs:
        column = attr.columns[0]
        if isinstance(column.type, SADateTime):
            keys.add(attr.key)
    return keys
