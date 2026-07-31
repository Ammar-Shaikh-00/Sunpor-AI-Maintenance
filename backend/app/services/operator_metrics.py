"""Live operator dashboard metrics from signal timeseries."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now_naive

from app.models.signal_catalog import SignalCatalog
from app.models.signal_timeseries import SignalTimeSeries

# Preferred WinCC tag fragments (longest/most specific first).
METRIC_TAG_PREFERENCES: dict[str, tuple[str, ...]] = {
    "pressure": (
        "E10L_MasseDruck",
        "MasseDruck",
        "melt_pressure",
    ),
    "torque": (
        "ExtruderDrehmoment",
        "Drehmoment",
        "torque",
    ),
    "throughput": (
        "GesamtDurchsatzIstwert",
        "GesamtDurchsatz",
        "DurchsatzIstwert",
    ),
}

METRIC_UNITS = {
    "pressure": "bar",
    "torque": "%",
    "throughput": "t/h",
}

METRIC_GROUPS = {
    "pressure": ("melt_pressure",),
    "torque": ("extruder_meltpump",),
    "throughput": ("feeders",),
}


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _scale_for_display(metric_key: str, value: float, unit: str | None) -> tuple[float, str]:
    """Convert kg/h throughput to t/h for the operator card."""
    normalized_unit = (unit or "").lower()
    if metric_key == "throughput":
        if normalized_unit in {"kg/h", "kgh", "kg / h"}:
            return round(value / 1000.0, 2), "t/h"
        if normalized_unit in {"t/h", "th"}:
            return round(value, 2), "t/h"
        # GesamtDurchsatz is typically kg/h even if unit missing.
        if value >= 50:
            return round(value / 1000.0, 2), "t/h"
        return round(value, 2), "t/h"
    if metric_key == "pressure":
        return round(value, 1), "bar"
    if metric_key == "torque":
        return round(value, 1), "%"
    return round(value, 2), METRIC_UNITS.get(metric_key, "")


def _find_catalog_signals(db: Session, metric_key: str) -> list[SignalCatalog]:
    preferences = METRIC_TAG_PREFERENCES[metric_key]
    catalogs = (
        db.query(SignalCatalog)
        .filter(SignalCatalog.active == True, SignalCatalog.is_deleted == False)  # noqa: E712
        .all()
    )

    matched: list[SignalCatalog] = []
    for preference in preferences:
        needle = preference.lower()
        hits = [
            item
            for item in catalogs
            if needle in (item.wincc_tag or "").lower()
            or needle in (item.display_name or "").lower()
        ]
        # Prefer actual roles when available.
        actuals = [item for item in hits if (item.signal_role or "").lower() == "actual"]
        chosen = actuals or hits
        if chosen:
            matched = chosen
            break

    if matched:
        return matched

    groups = METRIC_GROUPS[metric_key]
    return [
        item
        for item in catalogs
        if (item.signal_group or "") in groups
        and (item.signal_role or "").lower() in {"actual", ""}
    ]


def _history_for_signals(
    db: Session,
    signal_ids: list[int],
    start_time: datetime,
    end_time: datetime,
) -> list[tuple[datetime, float]]:
    if not signal_ids:
        return []

    rows = (
        db.query(SignalTimeSeries.timestamp, SignalTimeSeries.value_scaled, SignalTimeSeries.value_raw)
        .filter(
            SignalTimeSeries.signal_id.in_(signal_ids),
            SignalTimeSeries.timestamp >= start_time,
            SignalTimeSeries.timestamp <= end_time,
        )
        .order_by(SignalTimeSeries.timestamp.asc())
        .limit(4000)
        .all()
    )

    points: list[tuple[datetime, float]] = []
    for timestamp, value_scaled, value_raw in rows:
        value = _numeric(value_scaled)
        if value is None:
            value = _numeric(value_raw)
        if value is None:
            continue
        points.append((timestamp, value))
    return points


def _bucket_trend(
    points: list[tuple[datetime, float]],
    start_time: datetime,
    end_time: datetime,
    buckets: int = 12,
) -> list[float]:
    if not points or buckets <= 0:
        return []

    total_seconds = max(1.0, (end_time - start_time).total_seconds())
    bucket_width = total_seconds / buckets
    sums = [0.0] * buckets
    counts = [0] * buckets

    for timestamp, value in points:
        offset = (timestamp - start_time).total_seconds()
        index = min(buckets - 1, max(0, int(offset / bucket_width)))
        sums[index] += value
        counts[index] += 1

    trend: list[float] = []
    last = None
    for index in range(buckets):
        if counts[index]:
            last = sums[index] / counts[index]
            trend.append(last)
        elif last is not None:
            trend.append(last)
    return trend


def _delta_percent(points: list[tuple[datetime, float]], lookback_minutes: int = 8) -> float | None:
    if len(points) < 2:
        return None

    latest_ts, latest_val = points[-1]
    target = latest_ts - timedelta(minutes=lookback_minutes)
    baseline = None
    for timestamp, value in points:
        if timestamp <= target:
            baseline = value
        else:
            break

    if baseline is None:
        baseline = points[0][1]

    if baseline == 0:
        return None

    return round(((latest_val - baseline) / abs(baseline)) * 100.0, 1)


def build_operator_metrics(
    db: Session,
    window_minutes: int = 20,
    trend_buckets: int = 12,
) -> dict[str, Any]:
    end_time = utc_now_naive()
    start_time = end_time - timedelta(minutes=window_minutes)
    metrics: dict[str, Any] = {}

    for metric_key in ("pressure", "torque", "throughput"):
        catalogs = _find_catalog_signals(db, metric_key)
        signal_ids = [item.id for item in catalogs]
        unit_hint = catalogs[0].unit if catalogs else METRIC_UNITS[metric_key]
        points = _history_for_signals(db, signal_ids, start_time, end_time)

        raw_trend = _bucket_trend(points, start_time, end_time, trend_buckets)
        delta = _delta_percent(points)
        raw_value = points[-1][1] if points else None

        display_trend: list[float] = []
        display_value = None
        display_unit = METRIC_UNITS[metric_key]
        if raw_value is not None:
            display_value, display_unit = _scale_for_display(metric_key, raw_value, unit_hint)
        for sample in raw_trend:
            scaled, _ = _scale_for_display(metric_key, sample, unit_hint)
            display_trend.append(scaled)

        rising = None
        if delta is not None:
            rising = delta > 0

        metrics[metric_key] = {
            "value": display_value,
            "unit": display_unit,
            "delta_percent": delta,
            "rising": rising,
            "trend": display_trend,
            "window_minutes": window_minutes,
            "signal_count": len(signal_ids),
            "sample_count": len(points),
            "source_tags": [item.wincc_tag for item in catalogs[:5]],
        }

    return {
        "generated_at": end_time.isoformat(),
        "window_minutes": window_minutes,
        **metrics,
    }


def build_operator_notifications(
    db: Session,
    suggestions: list[dict[str, Any]],
    metrics: dict[str, Any],
    active_run_id: int | None,
) -> list[dict[str, Any]]:
    notifications: list[dict[str, Any]] = []

    for suggestion in suggestions:
        severity = suggestion.get("severity") or "info"
        if severity not in {"warning", "critical"}:
            continue
        notifications.append(
            {
                "id": f"suggestion:{suggestion.get('id')}",
                "severity": severity,
                "title": suggestion.get("title") or "Assistant alert",
                "message": suggestion.get("message") or "",
                "created_at": utc_now_naive().isoformat() + "Z",
                "kind": "suggestion",
            }
        )

    pressure = metrics.get("pressure") or {}
    if (
        pressure.get("delta_percent") is not None
        and pressure.get("delta_percent") >= 10
        and (pressure.get("value") or 0) >= 110
    ):
        notifications.append(
            {
                "id": "metric:pressure_rise",
                "severity": "warning",
                "title": "Melt pressure rising",
                "message": (
                    f"Pressure {pressure.get('value')} {pressure.get('unit')} "
                    f"({pressure.get('delta_percent'):+.1f}% over lookback)."
                ),
                "created_at": utc_now_naive().isoformat() + "Z",
                "kind": "metric",
            }
        )

    torque = metrics.get("torque") or {}
    if (
        torque.get("delta_percent") is not None
        and torque.get("delta_percent") >= 8
        and (torque.get("value") or 0) >= 60
    ):
        notifications.append(
            {
                "id": "metric:torque_rise",
                "severity": "warning",
                "title": "Extruder torque rising",
                "message": (
                    f"Torque {torque.get('value')}{torque.get('unit')} "
                    f"({torque.get('delta_percent'):+.1f}% over lookback)."
                ),
                "created_at": utc_now_naive().isoformat() + "Z",
                "kind": "metric",
            }
        )

    if active_run_id is None:
        notifications.append(
            {
                "id": "context:no_active_run",
                "severity": "warning",
                "title": "No active production run",
                "message": "Start a production run to continue operator capture.",
                "created_at": utc_now_naive().isoformat() + "Z",
                "kind": "context",
            }
        )

    # Stable unique order.
    seen = set()
    unique = []
    for item in notifications:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique[:10]
