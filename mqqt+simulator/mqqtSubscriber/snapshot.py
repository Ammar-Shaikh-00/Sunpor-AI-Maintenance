from datetime import datetime

import requests

from logging_config import setup_logging
from signal_cache import CachedSignalValue
from signal_cache import SignalValueCache

logger = setup_logging("snapshot")


def _build_payload(
    snapshot: dict[str, CachedSignalValue],
    tag_map: dict,
    snapshot_time: datetime,
) -> list[dict]:
    payload_values = []

    for wincc_tag, cached in snapshot.items():
        signal_meta = tag_map.get(wincc_tag)
        if not signal_meta:
            continue

        payload_values.append(
            {
                "signal_id": signal_meta["id"],
                "value_raw": cached.value_raw,
                "value_scaled": cached.value_scaled,
                "quality": cached.quality,
            }
        )

    missing_count = len(tag_map) - len(payload_values)
    if missing_count > 0:
        logger.debug(
            "Snapshot at %s includes %d/%d catalog signals (%d not received yet)",
            snapshot_time.isoformat(),
            len(payload_values),
            len(tag_map),
            missing_count,
        )

    return payload_values


def post_snapshot(
    cache: SignalValueCache,
    tag_map: dict,
    base_url: str,
    get_headers,
    refresh_headers,
) -> bool:
    """Post the current cache state to the backend batch endpoint."""

    snapshot = cache.snapshot()
    if not snapshot:
        logger.debug("Skipping snapshot because no MQTT values are cached yet")
        return False

    snapshot_time = datetime.utcnow()
    payload_values = _build_payload(snapshot, tag_map, snapshot_time)

    if not payload_values:
        logger.debug("Skipping snapshot because no valid signals found")
        return False

    payload = {
        "timestamp": snapshot_time.isoformat(),
        "source": "MQTT",
        "imported_at": snapshot_time.isoformat(),
        "values": payload_values,
    }

    response = requests.post(
        f"{base_url.rstrip('/')}/signal-timeseries/batch",
        json=payload,
        headers=get_headers(),
        timeout=60,
    )

    if response.status_code in (200, 201):
        body = response.json()
        logger.debug(
            "Snapshot saved | timestamp=%s | signals=%d | catalog=%d",
            snapshot_time.isoformat(),
            body.get("saved_count", len(payload_values)),
            len(tag_map),
        )
        return True

    logger.error(
        "Snapshot save failed | status=%s | response=%s",
        response.status_code,
        response.text,
    )
    refresh_headers()
    return False
