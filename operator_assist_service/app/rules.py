from __future__ import annotations

from pathlib import Path
from typing import Any

from app.rule_engine import RuleEngine, build_group_features

_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "rules_config.yaml"
_ENGINE = RuleEngine(_RULES_PATH)

# Operator-facing guidance derived from process phases in rules_config.yaml.
_PHASE_SUGGESTIONS: dict[str, dict[str, Any]] = {
    "fault_disturbance": {
        "id": "phase_fault_disturbance",
        "title": "Fault / disturbance likely",
        "message": (
            "Process rules indicate a fault or disturbance. "
            "Check heating, feeders, melt pump, and melt pressure."
        ),
        "severity": "critical",
        "horizon_minutes": 20,
        "suggested_event": {
            "level_1": "Malfunctions",
            "level_2": "Mechanical Malfunction",
            "level_3": "Other",
        },
    },
    "heating_up": {
        "id": "phase_heating_up",
        "title": "Heating up",
        "message": "Line appears to be heating up. Extruder/feeders not yet in production.",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {
            "level_1": "Extruder",
            "level_2": "Heating Up",
            "level_3": "Start",
        },
    },
    "startup": {
        "id": "phase_startup",
        "title": "Startup in progress",
        "message": "Screw is ramping and feeders are starting. Watch transition into stable production.",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {},
    },
    "stable_production": {
        "id": "phase_stable_production",
        "title": "Stable production",
        "message": "Process state looks like stable production on Extrusion E10.",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {},
    },
    "low_production": {
        "id": "phase_low_production",
        "title": "Low production",
        "message": "Throughput looks below stable range. Confirm material feed and setpoints.",
        "severity": "warning",
        "horizon_minutes": 30,
        "suggested_event": {
            "level_1": "Extruder",
            "level_2": "Low Production",
            "level_3": "Reason",
        },
    },
    "cleaning_run": {
        "id": "phase_cleaning_run",
        "title": "Cleaning run likely",
        "message": "Signals look like a cleaning run (process water active, feeders low).",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {
            "level_1": "Cleaning",
            "level_2": "Line Cleaning",
            "level_3": "Other",
        },
    },
    "empty_run": {
        "id": "phase_empty_run",
        "title": "Empty run likely",
        "message": "Extruder running with little/no feed and low melt pressure.",
        "severity": "warning",
        "horizon_minutes": 25,
        "suggested_event": {
            "level_1": "Extruder",
            "level_2": "Shutting Down",
            "level_3": "Empty",
        },
    },
    "cooling_down": {
        "id": "phase_cooling_down",
        "title": "Cooling down",
        "message": "Temperatures trending down and production signals are low.",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {},
    },
    "shutdown": {
        "id": "phase_shutdown",
        "title": "Shutdown / idle",
        "message": "Machine looks idle or shut down.",
        "severity": "info",
        "horizon_minutes": None,
        "suggested_event": {},
    },
}


def _enrich_with_metric_risk(
    suggestion: dict[str, Any],
    features: dict[str, float],
) -> dict[str, Any]:
    """Boost alert confidence/horizon when classic risk markers are present."""
    pressure = features.get("melt_pressure__mean_of_lasts")
    pressure_std = features.get("melt_pressure__mean_of_stds")
    confidence = float(suggestion.get("confidence") or 0)
    severity = suggestion.get("severity") or "info"
    horizon = suggestion.get("horizon_minutes")

    if pressure is not None and pressure >= 120:
        confidence = max(confidence, 0.72)
        if pressure >= 140:
            confidence = max(confidence, 0.85)
            severity = "critical"
            horizon = horizon or 20
            suggestion["title"] = "Possible screen blockage detected"
            suggestion["message"] = (
                "Melt pressure is elevated. Check the screen pack and material flow."
            )
            suggestion["suggested_event"] = {
                "level_1": "Extruder",
                "level_2": "Screen Change",
                "level_3": "Blocked",
            }

    if pressure_std is not None and pressure_std >= 30:
        confidence = max(confidence, 0.8)
        severity = "critical" if severity != "info" else severity
        horizon = horizon or 20

    suggestion["confidence"] = round(min(confidence, 0.95), 3)
    suggestion["severity"] = severity
    suggestion["horizon_minutes"] = horizon
    return suggestion


def analyze_signals(
    signals: list[dict[str, Any]],
    production_run_id: int | None = None,
    production_line_id: int | None = None,
) -> list[dict[str, Any]]:
    features = build_group_features(signals)
    result = _ENGINE.evaluate(features)
    template = _PHASE_SUGGESTIONS.get(
        result.phase_name,
        _PHASE_SUGGESTIONS["shutdown"],
    )

    confidence = result.confidence
    if result.is_fallback:
        confidence = 0.35
    elif result.is_confirmed_phase:
        confidence = max(confidence, 0.75)

    suggestion = {
        **template,
        "confidence": round(float(confidence), 3),
        "source": "operator_assist.rules_config",
        "phase": result.phase_name,
        "phase_index": result.phase_index,
        "is_fallback": result.is_fallback,
        "explanation": result.explanation,
        "feature_count": len(features),
    }
    suggestion = _enrich_with_metric_risk(suggestion, features)

    if production_line_id is not None:
        suggestion["production_line_id"] = production_line_id
    if production_run_id is not None:
        suggestion["production_run_id"] = production_run_id

    return [suggestion]
