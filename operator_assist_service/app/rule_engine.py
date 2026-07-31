"""Lightweight process-state rule engine for Operator Assist.

Loads phase rules from a local copy of AI_ML_Service/state/rules_config.yaml
(do not edit the original AI_ML_Service file). Thresholds live only in YAML.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_OPERATORS = {
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "eq": lambda a, b: a == b,
}


@dataclass
class StateResult:
    phase_name: str
    phase_index: int
    confidence: float
    conditions_met: int
    conditions_total: int
    is_fallback: bool
    is_confirmed_phase: bool
    explanation: str


class RuleEngine:
    def __init__(self, rules_config_path: str | Path) -> None:
        with open(rules_config_path, "r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)

        self._phases = config.get("phases", {})
        self._calibration = config.get("calibration_status", {})
        self._fallback_phase = config.get("fallback_phase", "shutdown")
        self._fallback_index = config.get("fallback_index", 7)
        self._ordered = sorted(
            self._phases.items(),
            key=lambda item: item[1].get("priority", 0),
            reverse=True,
        )

    def evaluate(self, group_features: dict[str, float]) -> StateResult:
        for phase_name, phase in self._ordered:
            conditions = phase.get("conditions", [])
            evaluated = 0
            passed = 0

            for condition in conditions:
                feature = condition.get("feature")
                if feature not in group_features:
                    continue
                evaluated += 1
                operator = _OPERATORS.get(condition.get("operator"))
                if operator and operator(
                    group_features[feature],
                    condition.get("threshold"),
                ):
                    passed += 1

            if evaluated == 0:
                continue

            ratio = passed / evaluated
            if ratio >= phase.get("min_conditions_ratio", 1.0):
                calibration = self._calibration.get(phase_name, "")
                return StateResult(
                    phase_name=phase_name,
                    phase_index=phase.get("index", -1),
                    confidence=round(ratio, 3),
                    conditions_met=passed,
                    conditions_total=evaluated,
                    is_fallback=False,
                    is_confirmed_phase="CONFIRMED" in str(calibration),
                    explanation=(
                        f"phase={phase_name} conf={ratio:.2f} "
                        f"calibration={calibration} "
                        f"conditions={passed}/{evaluated}"
                    ),
                )

        calibration = self._calibration.get(self._fallback_phase, "")
        return StateResult(
            phase_name=self._fallback_phase,
            phase_index=self._fallback_index,
            confidence=0.0,
            conditions_met=0,
            conditions_total=0,
            is_fallback=True,
            is_confirmed_phase="CONFIRMED" in str(calibration),
            explanation=(
                f"phase={self._fallback_phase} fallback=true "
                f"calibration={calibration} no_phase_matched"
            ),
        )


def build_group_features(signals: list[dict[str, Any]]) -> dict[str, float]:
    """Approximate group features from a latest-value snapshot.

    Full AI_ML window stats (trend/std/roc) are not available here yet, so we
    publish mean_of_lasts (+ hard/bad quality ratios when quality is present).
    Missing features are skipped by the rule engine.
    """
    buckets: dict[str, dict[str, Any]] = {}

    for signal in signals:
        group = (signal.get("signal_group") or "").strip()
        if not group:
            group = _infer_group(signal.get("wincc_tag") or "")
        if not group:
            continue

        value = _numeric(signal.get("value_scaled"))
        if value is None:
            value = _numeric(signal.get("value_raw"))
        if value is None:
            continue

        bucket = buckets.setdefault(
            group,
            {"lasts": [], "n": 0, "bad": 0, "hard": 0},
        )
        bucket["lasts"].append(value)
        bucket["n"] += 1

        quality = str(signal.get("quality") or "").upper()
        if quality and quality not in {"GOOD", ""}:
            bucket["bad"] += 1
        if quality in {"OUT_OF_RANGE", "BAD"}:
            bucket["hard"] += 1

    features: dict[str, float] = {}
    for group, bucket in buckets.items():
        lasts = bucket["lasts"]
        n = bucket["n"]
        if lasts:
            features[f"{group}__mean_of_lasts"] = sum(lasts) / len(lasts)
            # Snapshot variance proxy so melt_pressure__mean_of_stds can fire.
            if len(lasts) >= 2:
                mean = features[f"{group}__mean_of_lasts"]
                variance = sum((item - mean) ** 2 for item in lasts) / len(lasts)
                features[f"{group}__mean_of_stds"] = variance ** 0.5
            else:
                features[f"{group}__mean_of_stds"] = 0.0
            features[f"{group}__mean_of_trends"] = 0.0
        features[f"{group}__bad_quality_ratio"] = bucket["bad"] / n if n else 0.0
        features[f"{group}__hard_fault_ratio"] = bucket["hard"] / n if n else 0.0

    return features


def _numeric(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_group(wincc_tag: str) -> str:
    tag = wincc_tag.lower()
    if "massedruck" in tag or "melt_pressure" in tag:
        return "melt_pressure"
    if "drehmoment" in tag or "drehzahl" in tag or "extruder" in tag:
        return "extruder_meltpump"
    if "masse temperatur" in tag or "massetemperatur" in tag or "heating" in tag:
        return "heating_zones"
    if "feeder" in tag or "dosier" in tag:
        return "feeders"
    if "granulator" in tag or "messer" in tag:
        return "granulator"
    if "wasser" in tag or "water" in tag:
        return "process_water"
    if "status" in tag or "produktion" in tag:
        return "status"
    return ""
