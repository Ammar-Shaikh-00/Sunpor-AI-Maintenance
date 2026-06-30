"""Rule engine for process state detection.

Loads phase rules from YAML and evaluates aggregated group features against
them. All thresholds live in the YAML — there are zero business values in this
module. First phase (by priority) whose conditions pass wins; otherwise the
configured fallback phase is returned.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import yaml

logger = logging.getLogger(__name__)


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


def _op_gt(a, b):
    return a > b


def _op_lt(a, b):
    return a < b


def _op_gte(a, b):
    return a >= b


def _op_lte(a, b):
    return a <= b


def _op_eq(a, b):
    return a == b


_OPERATORS = {
    "gt": _op_gt,
    "lt": _op_lt,
    "gte": _op_gte,
    "lte": _op_lte,
    "eq": _op_eq,
}


class RuleEngine:
    """Evaluates group features against YAML-defined phase rules."""

    def __init__(self, rules_config_path: str) -> None:
        with open(rules_config_path, "r", encoding="utf-8") as fh:
            self._config = yaml.safe_load(fh)

        self._phases = self._config.get("phases", {})
        self._calibration = self._config.get("calibration_status", {})
        self._fallback_phase = self._config.get("fallback_phase", "shutdown")
        self._fallback_index = self._config.get("fallback_index", 7)
        self.min_vector_ready_ratio = self._config.get("min_vector_ready_ratio", 0.5)

        # Phases sorted by priority descending; first match wins.
        self._ordered = sorted(
            self._phases.items(),
            key=lambda kv: kv[1].get("priority", 0),
            reverse=True,
        )

    @property
    def confirmed_phases(self) -> list[str]:
        return [n for n, s in self._calibration.items() if "CONFIRMED" in str(s)]

    @property
    def estimated_phases(self) -> list[str]:
        return [n for n, s in self._calibration.items() if "CONFIRMED" not in str(s)]

    def apply_operator(self, val, op, threshold) -> bool:
        """Apply a comparison operator; unknown operator → False."""
        func = _OPERATORS.get(op)
        if func is None:
            logger.warning("Unknown operator '%s'", op)
            return False
        return func(val, threshold)

    def evaluate(self, group_features: dict) -> StateResult:
        """Return the first phase whose conditions pass, else the fallback."""
        for phase_name, phase in self._ordered:
            conditions = phase.get("conditions", [])
            evaluated = 0
            passed = 0
            for cond in conditions:
                feature = cond.get("feature")
                if feature not in group_features:
                    continue  # skip conditions whose feature is missing
                evaluated += 1
                if self.apply_operator(
                    group_features[feature], cond.get("operator"), cond.get("threshold")
                ):
                    passed += 1

            if evaluated == 0:
                continue

            ratio = passed / evaluated
            if ratio >= phase.get("min_conditions_ratio", 1.0):
                calibration = self._calibration.get(phase_name, "")
                is_confirmed = "CONFIRMED" in str(calibration)
                explanation = (
                    f"phase={phase_name} conf={ratio:.2f} "
                    f"calibration={calibration} "
                    f"conditions={passed}/{evaluated}"
                )
                return StateResult(
                    phase_name=phase_name,
                    phase_index=phase.get("index", -1),
                    confidence=round(ratio, 3),
                    conditions_met=passed,
                    conditions_total=evaluated,
                    is_fallback=False,
                    is_confirmed_phase=is_confirmed,
                    explanation=explanation,
                )

        # No phase matched → fallback.
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
