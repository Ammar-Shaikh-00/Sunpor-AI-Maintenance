"""Early Anomaly Detection (SUNPOR_Requirements_Document.docx, Section 7.2).

The single most-emphasized client pain point: dosing units start behaving
abnormally minutes before the extruder shows the effect, and today those
early signs are missed. This module catches abnormal behavior at the
source, even where no explicit rule exists, so operators can react before
an actual fault or scrap event (Section 1, Section 2.1).

Two stages, both implemented here:

1. Statistical baselines per phase — a rolling robust baseline (median +
   MAD) is kept per (phase, group, window, feature) key (see
   ``baseline_tracker.py``). Any group whose current value falls too far
   from that baseline (robust z-score) is flagged. Baselines are
   phase-specific: what is normal during startup is not normal during
   stable production. Process State (7.1) is a hard dependency.
2. Signal-specific drift detectors — a direct short-vs-long window
   comparison (e.g. 1min vs 30min) for a handful of priority
   group/feature pairs, to "flag creeping changes long before any
   threshold alarm" (Section 7.2), with no baseline history required.

Every finding — whichever stage produced it — is written with exactly one
``prediction_type``: ``"anomaly_score"``. Early Anomaly (7.2) is a
separate, earlier capability from the specific risk detections in Section
7.3 (Material Behavior), 7.5 (Granulator/Knife) and 7.6 (Nozzle/Screen) —
those are Phase 3 and have not been built yet, and this module's output
must never be mislabeled as one of them.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from anomaly.anomaly_writer import AnomalyWriter
from anomaly.baseline_tracker import BaselineTracker
from state.group_aggregator import GroupAggregator

logger = logging.getLogger(__name__)

TIER_WARNING = "WARNING"
TIER_CRITICAL = "CRITICAL"

METHOD_ZSCORE = "zscore"
METHOD_DRIFT_RATIO = "drift_ratio"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _confidence_from_score(abs_score: float, warning: float, critical: float) -> float:
    """Map a warning→critical span to a 0..1 confidence for dashboard ranking."""
    if critical <= warning:
        return 1.0
    ratio = (abs_score - warning) / (critical - warning)
    return round(min(max(ratio, 0.0), 1.0), 3)


@dataclass
class GroupAnomaly:
    """One anomaly finding — a group/window/feature deviating from normal."""

    prediction_type: str
    group_name: str
    window_key: str
    feature_name: str
    value: float
    score: float  # robust z-score (METHOD_ZSCORE) or relative drift ratio (METHOD_DRIFT_RATIO)
    method: str
    confidence: float
    tier: str
    phase_name: str
    is_derived: bool
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


def _load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


class AnomalyDetector:
    """Phase-aware statistical + drift anomaly detector (Section 7.2)."""

    def __init__(
        self,
        catalog: list[dict],
        config_path: str | Path,
        signal_client,
        auth_client,
        baseline_tracker: BaselineTracker | None = None,
    ) -> None:
        self._config = _load_config(config_path)
        self._prediction_type = self._config.get("anomaly_prediction_type", "anomaly_score")
        model_name = self._config.get("model_name", "anomaly_baseline_zscore_v1")
        self._predict_every = int(self._config.get("predict_every_n_polls", 3))

        self._scoring_windows: list[str] = self._config.get("scoring_windows", ["15min"])
        self._scored_features: list[str] = self._config.get(
            "scored_features", ["mean_of_means", "mean_of_stds"]
        )
        self._z_warning = float(self._config.get("z_score_warning", 3.0))
        self._z_critical = float(self._config.get("z_score_critical", 5.0))
        self._min_baseline_samples = int(self._config.get("min_baseline_samples", 20))
        self._score_only_confirmed = bool(
            self._config.get("score_only_confirmed_phases", True)
        )
        self._derived_features: list[dict] = self._config.get("derived_features", [])
        self._drift_detectors: list[dict] = self._config.get("drift_detectors", [])
        self._drift_warning = float(self._config.get("drift_ratio_warning", 0.15))
        self._drift_critical = float(self._config.get("drift_ratio_critical", 0.30))

        self._aggregator = GroupAggregator(catalog)
        self._role_of: dict[int, str] = {
            s["id"]: s.get("signal_role", "") for s in catalog if s.get("id") is not None
        }
        self._group_of: dict[int, str] = {
            s["id"]: s.get("signal_group", "") for s in catalog if s.get("id") is not None
        }
        self._baselines = baseline_tracker or BaselineTracker()
        self._writer = AnomalyWriter(signal_client, auth_client, model_name=model_name)

        self.last_findings: list[GroupAnomaly] = []
        self.history: deque = deque(maxlen=100)

    @property
    def prediction_type(self) -> str:
        return self._prediction_type

    # ── Pipeline entry point ──────────────────────────────────────────

    async def on_tick(
        self, vector, phase_name: str | None, is_confirmed_phase: bool, poll_count: int
    ) -> None:
        """Score the current vector and write findings (cadence-gated).

        Mirrors ``ProcessStateDetector.on_tick`` — never raises, gated by
        readiness and a poll cadence, and records a rolling history for
        the status endpoints.
        """
        if vector is None or not phase_name:
            return
        if self._predict_every <= 0 or poll_count % self._predict_every != 0:
            return

        try:
            findings = self.score(vector, phase_name, is_confirmed_phase)
            self.last_findings = findings

            written = 0
            for finding in findings:
                ok = await self._writer.write_finding(finding, vector)
                if ok:
                    written += 1

            self.history.append(
                {
                    "timestamp": _utcnow().isoformat(),
                    "phase_name": phase_name,
                    "is_confirmed_phase": is_confirmed_phase,
                    "findings_count": len(findings),
                    "written_count": written,
                    "tiers": {
                        TIER_WARNING: sum(1 for f in findings if f.tier == TIER_WARNING),
                        TIER_CRITICAL: sum(1 for f in findings if f.tier == TIER_CRITICAL),
                    },
                }
            )
            if findings:
                logger.info(
                    "[ANOMALY] phase=%s findings=%d written=%d",
                    phase_name,
                    len(findings),
                    written,
                )
        except Exception as exc:  # on_tick must never raise
            logger.error("AnomalyDetector.on_tick failed: %s", exc)

    # ── Scoring (pure — no I/O, safe to unit test directly) ───────────

    def score(
        self, vector, phase_name: str, is_confirmed_phase: bool
    ) -> list[GroupAnomaly]:
        """Update baselines and return anomaly findings for this tick.

        Baselines are updated for the current phase on every call (so
        every phase accrues its own "normal" over time, Section 7.2);
        findings are only produced when ``is_confirmed_phase`` is True (or
        gating is disabled in config) — matching Section 8's dashboard
        rule that these are "still... computed internally for learning
        purposes" even when suppressed from the dashboard.
        """
        findings: list[GroupAnomaly] = []
        if vector is None or not phase_name:
            return findings

        try:
            group_feats_by_window: dict[str, dict[str, dict[str, float]]] = {}

            for window_key in self._scoring_windows:
                wf = vector.windows.get(window_key)
                if wf is None or not wf.is_ready:
                    continue

                group_features = self._aggregator.aggregate(vector, window_key=window_key)
                by_group = self._group_by_prefix(group_features)
                group_feats_by_window[window_key] = by_group

                findings.extend(
                    self._score_group_features(
                        by_group, window_key, phase_name, is_confirmed_phase
                    )
                )
                findings.extend(
                    self._score_derived_features(
                        wf.signal_features, window_key, phase_name, is_confirmed_phase
                    )
                )

            findings.extend(
                self._score_drift_detectors(
                    group_feats_by_window, phase_name, is_confirmed_phase
                )
            )
        except Exception as exc:  # scoring must never raise
            logger.error("AnomalyDetector.score failed: %s", exc)
            return []

        return findings

    def get_status(self) -> dict:
        if not self.history:
            return {"status": "not_ready"}
        return {
            "findings_count": len(self.last_findings),
            "findings": [f.to_dict() for f in self.last_findings],
        }

    def get_history(self) -> list[dict]:
        return list(self.history)

    # ── Internal helpers ───────────────────────────────────────────────

    @staticmethod
    def _group_by_prefix(group_features: dict[str, float]) -> dict[str, dict[str, float]]:
        """Split ``{group}__{suffix}`` keys into {group: {suffix: value}}."""
        by_group: dict[str, dict[str, float]] = {}
        for key, value in group_features.items():
            if "__" not in key:
                continue
            group, suffix = key.split("__", 1)
            by_group.setdefault(group, {})[suffix] = value
        return by_group

    def _score_group_features(
        self,
        by_group: dict[str, dict[str, float]],
        window_key: str,
        phase_name: str,
        is_confirmed: bool,
    ) -> list[GroupAnomaly]:
        findings: list[GroupAnomaly] = []
        for group, feats in by_group.items():
            for feature_name in self._scored_features:
                value = feats.get(feature_name)
                if value is None:
                    continue
                finding = self._evaluate_zscore(
                    group, window_key, feature_name, value, phase_name, is_confirmed
                )
                if finding is not None:
                    findings.append(finding)
        return findings

    def _score_derived_features(
        self,
        signal_features: dict,
        window_key: str,
        phase_name: str,
        is_confirmed: bool,
    ) -> list[GroupAnomaly]:
        findings: list[GroupAnomaly] = []
        for spec in self._derived_features:
            name = spec.get("name")
            group = spec.get("group")
            role_a = spec.get("role_a")
            role_b = spec.get("role_b")
            if not (name and group and role_a and role_b):
                continue

            values_a, values_b = [], []
            for signal_id, sf in signal_features.items():
                if self._group_of.get(signal_id) != group or sf.last_val is None:
                    continue
                role = self._role_of.get(signal_id)
                if role == role_a:
                    values_a.append(sf.last_val)
                elif role == role_b:
                    values_b.append(sf.last_val)

            if not values_a or not values_b:
                continue

            gap = (sum(values_a) / len(values_a)) - (sum(values_b) / len(values_b))
            finding = self._evaluate_zscore(
                group, window_key, name, gap, phase_name, is_confirmed, is_derived=True
            )
            if finding is not None:
                findings.append(finding)
        return findings

    def _evaluate_zscore(
        self,
        group: str,
        window_key: str,
        feature_name: str,
        value: float,
        phase_name: str,
        is_confirmed: bool,
        is_derived: bool = False,
    ) -> GroupAnomaly | None:
        # Score against history collected BEFORE this observation, then
        # update — the current point is never part of its own baseline.
        n_before = self._baselines.sample_count(phase_name, group, window_key, feature_name)
        z = self._baselines.score(phase_name, group, window_key, feature_name, value)
        self._baselines.update(phase_name, group, window_key, feature_name, value)

        if self._score_only_confirmed and not is_confirmed:
            return None
        if n_before < self._min_baseline_samples or z is None:
            return None

        abs_z = abs(z)
        if abs_z >= self._z_critical:
            tier = TIER_CRITICAL
        elif abs_z >= self._z_warning:
            tier = TIER_WARNING
        else:
            return None

        kind = "derived feature" if is_derived else "feature"
        explanation = (
            f"anomaly group={group} window={window_key} {kind}={feature_name} "
            f"value={value:.4f} z={z:.2f} tier={tier} phase={phase_name}"
        )
        return GroupAnomaly(
            prediction_type=self._prediction_type,
            group_name=group,
            window_key=window_key,
            feature_name=feature_name,
            value=round(float(value), 4),
            score=round(z, 3),
            method=METHOD_ZSCORE,
            confidence=_confidence_from_score(abs_z, self._z_warning, self._z_critical),
            tier=tier,
            phase_name=phase_name,
            is_derived=is_derived,
            explanation=explanation,
        )

    def _score_drift_detectors(
        self,
        group_feats_by_window: dict[str, dict[str, dict[str, float]]],
        phase_name: str,
        is_confirmed: bool,
    ) -> list[GroupAnomaly]:
        if self._score_only_confirmed and not is_confirmed:
            return []

        findings: list[GroupAnomaly] = []
        for spec in self._drift_detectors:
            group = spec.get("group")
            feature = spec.get("feature")
            short_key = spec.get("short_window")
            long_key = spec.get("long_window")
            if not (group and feature and short_key and long_key):
                continue

            short_val = group_feats_by_window.get(short_key, {}).get(group, {}).get(feature)
            long_val = group_feats_by_window.get(long_key, {}).get(group, {}).get(feature)
            if short_val is None or long_val is None:
                continue

            denom = max(abs(long_val), 1e-6)
            ratio = (short_val - long_val) / denom
            abs_ratio = abs(ratio)
            if abs_ratio >= self._drift_critical:
                tier = TIER_CRITICAL
            elif abs_ratio >= self._drift_warning:
                tier = TIER_WARNING
            else:
                continue

            explanation = (
                f"drift group={group} feature={feature} "
                f"short[{short_key}]={short_val:.4f} long[{long_key}]={long_val:.4f} "
                f"ratio={ratio:.3f} tier={tier} phase={phase_name}"
            )
            findings.append(
                GroupAnomaly(
                    prediction_type=self._prediction_type,
                    group_name=group,
                    window_key=short_key,
                    feature_name=f"{feature}_drift_vs_{long_key}",
                    value=round(float(short_val), 4),
                    score=round(ratio, 4),
                    method=METHOD_DRIFT_RATIO,
                    confidence=_confidence_from_score(
                        abs_ratio, self._drift_warning, self._drift_critical
                    ),
                    tier=tier,
                    phase_name=phase_name,
                    is_derived=True,
                    explanation=explanation,
                )
            )
        return findings
