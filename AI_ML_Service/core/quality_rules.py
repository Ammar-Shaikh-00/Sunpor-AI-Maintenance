"""Data-quality evaluation for incoming signal values.

Produces the ``quality`` tag written into each batch payload value. Tags match
the backend schema. Range bounds are defined per *signal_group* (never per
individual signal). The lower bound is relaxed for ``control_output`` roles
only — PID heating outputs may be negative; measurements (actual, pressure,
throughput, etc.) still require non-negative values.
"""

from __future__ import annotations

from typing import Optional

from core.config import get_settings

# Quality tags (string values must match the backend schema).
GOOD = "GOOD"
STALE = "STALE"
OUT_OF_RANGE = "OUT_OF_RANGE"
MISSING = "MISSING"
BAD = "BAD"

# Physically safe min/max on the RAW scale, per signal_group. These are the
# only tunable values; they are deliberately broad sanity limits, not
# per-signal calibration.
SIGNAL_GROUP_BOUNDS: dict[str, tuple[float, float]] = {
    "heating_zones": (0, 5000),
    "feeders": (0, 50000),
    "screen_changer": (0, 10000),
    "process_water": (0, 10000),
    "granulator": (0, 10000),
    "melt_pressure": (0, 10000),
    "offspec": (0, 10000),
    "pentane_nitrogen": (0, 10000),
    "extruder_meltpump": (0, 10000),
    "status": (0, 100),
}

# PID control outputs (e.g. heating zone Stellgröße) may be negative.
# This overrides the group min (0) for that role only — values are never
# flipped; we simply do not flag legitimate negative control output as OOR.
CONTROL_OUTPUT_MIN = -5000

# Roles allowed to use CONTROL_OUTPUT_MIN instead of the group minimum.
NEGATIVE_ALLOWED_ROLES = frozenset({"control_output"})


class QualityEvaluator:
    """Assigns a quality tag to each incoming raw signal value."""

    def __init__(self, catalog: list[dict], stale_count: Optional[int] = None) -> None:
        if stale_count is None:
            stale_count = get_settings().STALE_COUNT
        self._stale_count = stale_count

        # signal_id -> {group, role, factor, min, max}  (bounds on raw scale)
        self._lookup: dict[int, dict] = {}
        # signal_id -> (last_value, consecutive_identical_count)
        self._stale_tracker: dict[int, tuple[Optional[float], int]] = {}

        for signal in catalog:
            signal_id = signal.get("id")
            if signal_id is None:
                continue
            group = signal.get("signal_group")
            role = signal.get("signal_role", "")
            factor = signal.get("factor", 1) or 1
            bound_min, bound_max = SIGNAL_GROUP_BOUNDS.get(group, (None, None))
            if role in NEGATIVE_ALLOWED_ROLES and bound_min is not None:
                bound_min = CONTROL_OUTPUT_MIN
            self._lookup[signal_id] = {
                "group": group,
                "role": role,
                "factor": factor,
                "min": bound_min,
                "max": bound_max,
            }

    def evaluate(self, signal_id: int, value_raw: float) -> str:
        """Return the quality tag for a single raw value."""
        info = self._lookup.get(signal_id)

        # Track consecutive identical values for staleness detection.
        last_value, count = self._stale_tracker.get(signal_id, (None, 0))
        count = count + 1 if last_value == value_raw else 1
        self._stale_tracker[signal_id] = (value_raw, count)

        # 1) Range check (bounds × factor, compared on the raw scale).
        if info and info["min"] is not None and info["max"] is not None:
            factor = info["factor"]
            raw_min = info["min"] * factor
            raw_max = info["max"] * factor
            if value_raw < raw_min or value_raw > raw_max:
                return OUT_OF_RANGE

        # 2) Staleness check.
        if count >= self._stale_count:
            return STALE

        return GOOD

    def mark_missing(self, signal_id: int) -> str:
        """Flag a signal as missing for this poll and reset its stale tracker."""
        self._stale_tracker[signal_id] = (None, 0)
        return MISSING
