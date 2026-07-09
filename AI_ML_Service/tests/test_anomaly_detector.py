"""Unit tests for Early Anomaly Detection (Section 7.2).

Loads the real anomaly/anomaly_config.yaml so threshold changes are
exercised by the suite, same convention as test_rule_engine.py for
state/rules_config.yaml.
"""

from __future__ import annotations

import itertools
import os
from datetime import datetime, timezone

from anomaly.detector import (
    METHOD_DRIFT_RATIO,
    METHOD_ZSCORE,
    TIER_CRITICAL,
    TIER_WARNING,
    AnomalyDetector,
)
from features.models import FeatureVector, SignalFeatures, WindowFeatures

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "anomaly", "anomaly_config.yaml"
)

_WINDOWS = ("1min", "15min", "30min")


def _catalog() -> list[dict]:
    return [
        {"id": 1, "signal_group": "feeders", "signal_role": "actual"},
        {"id": 2, "signal_group": "feeders", "signal_role": "actual"},
        {"id": 3, "signal_group": "feeders", "signal_role": "setpoint"},
        {"id": 4, "signal_group": "feeders", "signal_role": "setpoint"},
        {"id": 5, "signal_group": "heating_zones", "signal_role": "actual"},
        {"id": 6, "signal_group": "melt_pressure", "signal_role": "actual"},
        {"id": 7, "signal_group": "extruder_meltpump", "signal_role": "actual"},
        {"id": 8, "signal_group": "extruder_meltpump", "signal_role": "setpoint"},
    ]


def _detector() -> AnomalyDetector:
    return AnomalyDetector(_catalog(), CONFIG_PATH, signal_client=None, auth_client=None)


def _sf(signal_id, group, last_val, mean=None, std=0.0, trend=0.0, roc=0.0):
    m = last_val if mean is None else mean
    return SignalFeatures(
        signal_id=signal_id,
        signal_group=group,
        mean=m,
        std=std,
        trend=trend,
        roc=roc,
        min_val=last_val,
        max_val=last_val,
        last_val=last_val,
        sample_count=90,
        has_bad_quality=False,
        has_hard_fault=False,
    )


def _wf(signal_map: dict, window_key: str, std_by_group: dict | None = None) -> WindowFeatures:
    return WindowFeatures(
        window_key=window_key,
        sample_count=90,
        signal_features=signal_map,
        is_ready=True,
        ready_ratio=1.0,
    )


def _vector(signal_map: dict, windows=_WINDOWS) -> FeatureVector:
    return FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={w: _wf(signal_map, w) for w in windows},
        is_ready=True,
    )


def _baseline_signal_map(feeders_val=300.0, heating_val=200.0, melt_val=100.0):
    """A stable, near-identical reading for every signal in the catalog."""
    return {
        1: _sf(1, "feeders", feeders_val),
        2: _sf(2, "feeders", feeders_val),
        3: _sf(3, "feeders", feeders_val),
        4: _sf(4, "feeders", feeders_val),
        5: _sf(5, "heating_zones", heating_val),
        6: _sf(6, "melt_pressure", melt_val),
        7: _sf(7, "extruder_meltpump", 50.0),
        8: _sf(8, "extruder_meltpump", 50.0),
    }


def _feed_baseline(detector: AnomalyDetector, n: int = 25, phase="stable_production", confirmed=True):
    """Feed n slightly-varying stable observations to build up a real baseline."""
    offsets = itertools.cycle([-2, -1, 0, 1, 2])
    for _ in range(n):
        off = next(offsets)
        signal_map = _baseline_signal_map(feeders_val=300.0 + off, heating_val=200.0 + off)
        detector.score(_vector(signal_map), phase, confirmed)


def test_prediction_type_is_always_anomaly_score():
    detector = _detector()
    _feed_baseline(detector)

    outlier_map = _baseline_signal_map()
    outlier_map[5] = _sf(5, "heating_zones", 900.0)  # heating way outside its baseline
    findings = detector.score(_vector(outlier_map), "stable_production", True)

    assert len(findings) > 0
    assert all(f.prediction_type == "anomaly_score" for f in findings)


def test_no_findings_before_min_baseline_samples():
    detector = _detector()
    # Only a handful of observations — well under min_baseline_samples (20).
    _feed_baseline(detector, n=5)

    outlier_map = _baseline_signal_map()
    outlier_map[5] = _sf(5, "heating_zones", 900.0)
    findings = detector.score(_vector(outlier_map), "stable_production", True)

    assert findings == []


def test_finding_emitted_after_baseline_and_deviation():
    detector = _detector()
    _feed_baseline(detector)

    outlier_map = _baseline_signal_map()
    outlier_map[5] = _sf(5, "heating_zones", 900.0)
    findings = detector.score(_vector(outlier_map), "stable_production", True)

    heating_findings = [f for f in findings if f.group_name == "heating_zones"]
    assert heating_findings
    assert any(f.method == METHOD_ZSCORE for f in heating_findings)
    assert any(f.tier in (TIER_WARNING, TIER_CRITICAL) for f in heating_findings)


def test_scoring_gated_by_confirmed_phase():
    detector = _detector()
    # Baseline built while phase is NOT confirmed -> baseline still updates...
    _feed_baseline(detector, n=25, phase="stable_production", confirmed=False)

    outlier_map = _baseline_signal_map()
    outlier_map[5] = _sf(5, "heating_zones", 900.0)

    # ...but no findings are produced while unconfirmed.
    findings_unconfirmed = detector.score(_vector(outlier_map), "stable_production", False)
    assert findings_unconfirmed == []

    # Once confirmed, the same accumulated baseline produces findings.
    findings_confirmed = detector.score(_vector(outlier_map), "stable_production", True)
    assert any(f.group_name == "heating_zones" for f in findings_confirmed)


def test_derived_feature_gap_detected():
    detector = _detector()
    # Baseline: actual == setpoint for feeders (gap ~0).
    _feed_baseline(detector)

    # Now push a big actual-vs-setpoint mismatch (unstable dosing).
    mismatch_map = _baseline_signal_map()
    mismatch_map[1] = _sf(1, "feeders", 900.0)
    mismatch_map[2] = _sf(2, "feeders", 900.0)
    findings = detector.score(_vector(mismatch_map), "stable_production", True)

    derived = [f for f in findings if f.feature_name == "feeders_setpoint_actual_gap"]
    assert derived
    assert all(f.prediction_type == "anomaly_score" for f in derived)
    assert all(f.is_derived for f in derived)


def test_explanation_contains_group_and_feature_name():
    detector = _detector()
    _feed_baseline(detector)

    outlier_map = _baseline_signal_map()
    outlier_map[5] = _sf(5, "heating_zones", 900.0)
    findings = detector.score(_vector(outlier_map), "stable_production", True)

    heating_findings = [f for f in findings if f.group_name == "heating_zones"]
    assert heating_findings
    for f in heating_findings:
        assert f.group_name in f.explanation
        assert f.feature_name in f.explanation


def test_drift_detector_flags_short_vs_long_window_divergence():
    detector = _detector()
    _feed_baseline(detector)

    # Long windows (15min/30min) stay at the stable baseline; only the
    # 1min window spikes -> a pure short-vs-long drift, no baseline needed.
    stable_map = _baseline_signal_map()
    drifted_map = _baseline_signal_map()
    drifted_map[1] = _sf(1, "feeders", 900.0)
    drifted_map[2] = _sf(2, "feeders", 900.0)

    vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={
            "1min": _wf(drifted_map, "1min"),
            "15min": _wf(stable_map, "15min"),
            "30min": _wf(stable_map, "30min"),
        },
        is_ready=True,
    )
    findings = detector.score(vector, "stable_production", True)

    drift_findings = [f for f in findings if f.method == METHOD_DRIFT_RATIO]
    assert drift_findings
    assert all(f.prediction_type == "anomaly_score" for f in drift_findings)
    assert any(f.group_name == "feeders" for f in drift_findings)


def test_score_never_raises_on_empty_vector():
    detector = _detector()
    empty_vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={},
        is_ready=False,
    )
    assert detector.score(empty_vector, "stable_production", True) == []
    assert detector.score(None, "stable_production", True) == []
    assert detector.score(empty_vector, "", True) == []
