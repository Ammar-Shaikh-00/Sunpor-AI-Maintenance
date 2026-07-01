"""Data-quality evaluation for incoming signal values.

Produces the ``quality`` tag written into each batch payload value. Tags match
the backend schema. Range bounds are looked up via a role-first / group+role
combined key strategy — never per individual signal.

Bounds in ``SIGNAL_GROUP_ROLE_BOUNDS`` and ``SIGNAL_ROLE_BOUNDS`` are defined
in physical/engineering units (°C, bar, RPM, kg/h). The range check compares
``value_raw × factor`` (i.e. the scaled value) against those limits.

Lookup priority (highest wins):

1. ``SIGNAL_GROUP_ROLE_BOUNDS[(signal_group, signal_role)]``
2. ``SIGNAL_ROLE_BOUNDS[signal_role]``
3. No match → skip range check (``GOOD`` unless staleness applies)
"""

from __future__ import annotations

from typing import Optional

from core.config import get_settings

GOOD = "GOOD"
STALE = "STALE"
OUT_OF_RANGE = "OUT_OF_RANGE"
MISSING = "MISSING"
BAD = "BAD"

# Role-only bounds — apply to ALL signals of this role regardless of group.
SIGNAL_ROLE_BOUNDS: dict[str, tuple[float, float]] = {
    "control_output": (-110.0, 110.0),
    "error": (0.0, 9999.0),
    "mode": (0.0, 99.0),
    "status": (0.0, 1.0),
}

# (signal_group, signal_role) combined key — physical limits per group+role.
SIGNAL_GROUP_ROLE_BOUNDS: dict[tuple[str, str], tuple[float, float]] = {
    ("heating_zones", "actual"): (0.0, 350.0),
    ("heating_zones", "setpoint"): (0.0, 350.0),
    ("feeders", "actual"): (0.0, 20000.0),
    ("feeders", "setpoint"): (0.0, 20000.0),
    ("feeders", "quantity"): (0.0, 999999.0),
    ("melt_pressure", "actual"): (0.0, 500.0),
    ("melt_pressure", "setpoint"): (0.0, 500.0),
    ("screen_changer", "actual"): (0.0, 400.0),
    ("screen_changer", "setpoint"): (0.0, 400.0),
    ("extruder_meltpump", "actual"): (0.0, 200.0),
    ("extruder_meltpump", "setpoint"): (0.0, 200.0),
    ("granulator", "actual"): (0.0, 2000.0),
    ("granulator", "setpoint"): (0.0, 2000.0),
    ("process_water", "actual"): (0.0, 200.0),
    ("process_water", "setpoint"): (0.0, 200.0),
    ("pentane_nitrogen", "actual"): (0.0, 500.0),
    ("offspec", "quantity"): (0.0, 999999.0),
}


def _lookup_bounds(
    group: str, role: str
) -> Optional[tuple[float, float]]:
    """Return bounds for a (group, role) pair using the documented priority."""
    combined = SIGNAL_GROUP_ROLE_BOUNDS.get((group, role))
    if combined is not None:
        return combined
    return SIGNAL_ROLE_BOUNDS.get(role)


class QualityEvaluator:
    """Assigns a quality tag to each incoming raw signal value."""

    def __init__(
        self, catalog: list[dict], stale_count: Optional[int] = None
    ) -> None:
        settings = get_settings()
        if stale_count is None:
            stale_count = settings.STALE_COUNT
        self._stale_count = stale_count
        self._stale_exempt_roles = set(settings.STALE_EXEMPT_ROLES)

        # signal_id -> {signal_group, signal_role, factor}
        self._catalog_map: dict[int, dict] = {}
        # signal_id -> (last_value, consecutive_identical_count)
        self._stale_tracker: dict[int, tuple[Optional[float], int]] = {}

        for signal in catalog:
            signal_id = signal.get("id")
            if signal_id is None:
                continue
            self._catalog_map[signal_id] = {
                "signal_group": signal.get("signal_group", "") or "",
                "signal_role": signal.get("signal_role", "") or "",
                "factor": signal.get("factor", 1) or 1,
            }

    def evaluate(self, signal_id: int, value_raw: float) -> str:
        """Return the quality tag for a single raw value."""
        info = self._catalog_map.get(signal_id)
        if info is None:
            return GOOD

        group = info["signal_group"]
        role = info["signal_role"]
        factor = info["factor"]

        # 1) Bounds check — on scaled value (physical units).
        bounds = _lookup_bounds(group, role)
        if bounds is not None:
            value_for_check = round(value_raw * factor, 4)
            lo, hi = bounds
            if not (lo <= value_for_check <= hi):
                return OUT_OF_RANGE

        # 2) Stale check — skip exempt roles (setpoint, mode, status, quantity).
        if role in self._stale_exempt_roles:
            return GOOD

        last_val, count = self._stale_tracker.get(signal_id, (None, 0))
        if last_val is not None and value_raw == last_val:
            count += 1
            self._stale_tracker[signal_id] = (value_raw, count)
            if count >= self._stale_count:
                return STALE
        else:
            count = 1
            self._stale_tracker[signal_id] = (value_raw, count)

        return GOOD

    def mark_missing(self, signal_id: int) -> str:
        """Flag a signal as missing for this poll and reset its stale tracker."""
        self._stale_tracker[signal_id] = (None, 0)
        return MISSING
