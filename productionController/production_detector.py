"""Sensor-based 'is production active?' evaluation.

Uses catalog group/role + latest timeseries values only — no process_state
ML predictions (those require an existing run and cannot bootstrap).

Catalog rows are scoped by production_line_id (signal_catalog FK) so each
line is evaluated only on its own WinCC signals.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

_OPS = {
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


def _mean(values: list[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def filter_catalog_for_line(
    catalog: list[dict],
    production_line_id: int,
    *,
    active_only: bool = True,
) -> list[dict]:
    """Keep catalog rows linked to this production line via signal_catalog."""
    out: list[dict] = []
    for row in catalog:
        if row.get("production_line_id") is None:
            continue
        if int(row["production_line_id"]) != int(production_line_id):
            continue
        if active_only and row.get("active") is False:
            continue
        if row.get("is_deleted") is True:
            continue
        out.append(row)
    return out


def evaluate_production_active(
    catalog: list[dict],
    latest: list[dict],
    pc_config: dict,
    *,
    production_line_id: int | None = None,
) -> tuple[bool, dict[str, Any]]:
    """Return (is_active, debug_info) from a latest signal snapshot.

    catalog items need: id, signal_group, signal_role [, production_line_id]
    latest items need: signal_id, value_scaled, quality

    When production_line_id is set, only that line's catalog signals are used.
    """
    if production_line_id is not None:
        catalog = filter_catalog_for_line(catalog, production_line_id)

    rule = pc_config.get("production_active") or {}
    conditions = rule.get("conditions") or []
    min_ratio = float(rule.get("min_conditions_ratio", 1.0))
    require_good = bool(rule.get("require_good_quality", True))

    if not conditions:
        return False, {
            "reason": "no_conditions_configured",
            "production_line_id": production_line_id,
        }

    if not catalog:
        return False, {
            "reason": "no_signals_for_line",
            "production_line_id": production_line_id,
        }

    by_id = {int(s["id"]): s for s in catalog if s.get("id") is not None}
    latest_by_id: dict[int, dict] = {}
    for row in latest:
        sid = row.get("signal_id")
        if sid is None:
            continue
        latest_by_id[int(sid)] = row

    passed = 0
    evaluated = 0
    details: list[dict] = []

    for cond in conditions:
        group = cond.get("group")
        role = cond.get("role")  # None / null / "" → any role in group
        op_name = cond.get("operator", "gte")
        threshold = float(cond.get("threshold", 0.0))
        op = _OPS.get(op_name)
        if not group or op is None:
            details.append({"group": group, "skipped": "bad_condition"})
            continue

        values: list[float] = []
        for sid, meta in by_id.items():
            if meta.get("signal_group") != group:
                continue
            if role not in (None, "", "null") and meta.get("signal_role") != role:
                continue
            row = latest_by_id.get(sid)
            if row is None:
                continue
            if require_good and str(row.get("quality", "GOOD")).upper() != "GOOD":
                continue
            raw = row.get("value_scaled")
            if raw is None:
                raw = row.get("value_raw")
            if raw is None:
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue

        agg = _mean(values)
        evaluated += 1
        ok = agg is not None and op(agg, threshold)
        if ok:
            passed += 1
        details.append(
            {
                "group": group,
                "role": role,
                "n_signals": len(values),
                "mean": None if agg is None else round(agg, 3),
                "operator": op_name,
                "threshold": threshold,
                "passed": ok,
            }
        )

    if evaluated == 0:
        return False, {
            "reason": "no_conditions_evaluated",
            "production_line_id": production_line_id,
            "details": details,
        }

    ratio = passed / evaluated
    is_active = ratio >= min_ratio
    info = {
        "is_active": is_active,
        "production_line_id": production_line_id,
        "passed": passed,
        "evaluated": evaluated,
        "ratio": round(ratio, 3),
        "min_ratio": min_ratio,
        "catalog_signals": len(catalog),
        "details": details,
    }
    logger.debug("production_active eval: %s", info)
    return is_active, info
