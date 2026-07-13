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
    METHOD_ABSOLUTE_THRESHOLD,
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


# ─── Stage 0 — absolute safety thresholds ─────────────────────────────


def _catalog_with_process_water() -> list[dict]:
    return _catalog() + [
        {
            "id": 9,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Temperatur",
        },
    ]


def _detector_with_process_water() -> AnomalyDetector:
    return AnomalyDetector(
        _catalog_with_process_water(), CONFIG_PATH, signal_client=None, auth_client=None
    )


def _process_water_vector(last_val: float) -> FeatureVector:
    """1min window with a single process_water/actual temperature reading."""
    signal_map = {9: _sf(9, "process_water", last_val)}
    return FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={"1min": _wf(signal_map, "1min")},
        is_ready=True,
    )


def test_process_water_alarm_fires_above_64():
    detector = _detector_with_process_water()
    findings = detector.score(_process_water_vector(66.0), "startup", False)

    alarm = [f for f in findings if f.group_name == "process_water_temp_alarm"]
    assert len(alarm) == 1
    assert alarm[0].tier == TIER_WARNING
    assert alarm[0].method == METHOD_ABSOLUTE_THRESHOLD
    assert alarm[0].prediction_type == "anomaly_score"
    assert alarm[0].confidence == 1.0


def test_process_water_critical_fires_above_65():
    detector = _detector_with_process_water()
    findings = detector.score(_process_water_vector(66.0), "stable_production", True)

    names = {f.group_name for f in findings if f.method == METHOD_ABSOLUTE_THRESHOLD}
    assert "process_water_temp_alarm" in names
    assert "process_water_temp_critical" in names
    critical = [f for f in findings if f.group_name == "process_water_temp_critical"]
    assert critical[0].tier == TIER_CRITICAL


def test_absolute_threshold_ignores_confirmed_phase_gate():
    detector = _detector_with_process_water()
    assert detector._score_only_confirmed is True

    findings = detector.score(_process_water_vector(66.0), "startup", False)

    absolute = [f for f in findings if f.method == METHOD_ABSOLUTE_THRESHOLD]
    assert any(f.group_name == "process_water_temp_alarm" for f in absolute)
    # Stage 1/2 must stay silent without a confirmed phase / baseline.
    assert all(f.method == METHOD_ABSOLUTE_THRESHOLD for f in findings)


def test_absolute_threshold_below_normal_no_fire():
    detector = _detector_with_process_water()
    findings = detector.score(_process_water_vector(59.0), "stable_production", True)

    absolute = [f for f in findings if f.method == METHOD_ABSOLUTE_THRESHOLD]
    assert absolute == []


def test_temp_alarm_checks_both_temperature_sensors():
    catalog = _catalog() + [
        {
            "id": 9,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Temperatur",
        },
        {
            "id": 10,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10I203_temp",
        },
        {
            "id": 11,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Drehzahl",
        },
    ]
    detector = AnomalyDetector(catalog, CONFIG_PATH, signal_client=None, auth_client=None)
    signal_map = {
        9: _sf(9, "process_water", 59.7),
        10: _sf(10, "process_water", 66.0),
        11: _sf(11, "process_water", 90.0),  # pump speed — must be excluded
    }
    vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={"1min": _wf(signal_map, "1min")},
        is_ready=True,
    )
    findings = detector.score(vector, "startup", False)

    alarm = [f for f in findings if f.group_name == "process_water_temp_alarm"]
    assert len(alarm) == 1
    assert alarm[0].value == 66.0  # max of temps, not pump 90.0
    assert alarm[0].tier == TIER_WARNING


def test_pressure_low_checks_both_pressure_sensors():
    catalog = _catalog() + [
        {
            "id": 12,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Druck1",
        },
        {
            "id": 13,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Druck2",
        },
    ]
    detector = AnomalyDetector(catalog, CONFIG_PATH, signal_client=None, auth_client=None)
    signal_map = {
        12: _sf(12, "process_water", 10.5),
        13: _sf(13, "process_water", 9.8),
    }
    vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={"1min": _wf(signal_map, "1min")},
        is_ready=True,
    )
    findings = detector.score(vector, "stable_production", True)

    pressure = [f for f in findings if f.group_name == "process_water_pressure_low"]
    assert len(pressure) == 1
    assert pressure[0].value == 9.8
    assert pressure[0].tier == TIER_WARNING


def test_pump_speed_never_included_in_temp_check():
    catalog = _catalog() + [
        {
            "id": 11,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Drehzahl",
        },
    ]
    detector = AnomalyDetector(catalog, CONFIG_PATH, signal_client=None, auth_client=None)
    signal_map = {11: _sf(11, "process_water", 90.0)}
    vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={"1min": _wf(signal_map, "1min")},
        is_ready=True,
    )
    findings = detector.score(vector, "startup", False)

    absolute = [f for f in findings if f.method == METHOD_ABSOLUTE_THRESHOLD]
    assert absolute == []


def test_empty_match_warns_once_not_every_poll(caplog):
    import logging

    catalog = _catalog() + [
        {
            "id": 11,
            "signal_group": "process_water",
            "signal_role": "actual",
            "wincc_tag": "EX10_Prozesswasser_Drehzahl",
        },
    ]
    detector = AnomalyDetector(catalog, CONFIG_PATH, signal_client=None, auth_client=None)
    signal_map = {11: _sf(11, "process_water", 90.0)}
    vector = FeatureVector(
        model_key="anomaly",
        timestamp=datetime.now(timezone.utc),
        windows={"1min": _wf(signal_map, "1min")},
        is_ready=True,
    )

    with caplog.at_level(logging.WARNING, logger="anomaly.detector"):
        for _ in range(3):
            detector._check_absolute_thresholds(vector, "startup")

    warn_msgs = [
        r.message
        for r in caplog.records
        if r.levelno == logging.WARNING and "absolute_threshold=" in r.message
    ]
    # One warning per threshold name that had an empty match (temp alarm,
    # temp critical, pressure) — not repeated across the 3 polls.
    assert len(warn_msgs) == 3
    assert len(set(warn_msgs)) == 3
    assert "process_water_temp_alarm" in detector._empty_match_warned
    assert "process_water_temp_critical" in detector._empty_match_warned
    assert "process_water_pressure_low" in detector._empty_match_warned


# ─── Write cooldown (throttles /ml-predictions only) ──────────────────


def test_cooldown_blocks_repeat_write_within_window():
    detector = _detector()
    assert detector._write_cooldown_polls == 18

    assert detector.should_write("process_water_temp_alarm", 10) is True
    assert detector.should_write("process_water_temp_alarm", 15) is False
    assert detector.should_write("process_water_temp_alarm", 28) is True  # 18+ later


def test_cooldown_independent_per_finding_name():
    detector = _detector()

    assert detector.should_write("process_water_temp_alarm", 10) is True
    assert detector.should_write("melt_pressure", 10) is True  # different key, own timer
    assert detector.should_write("process_water_temp_alarm", 12) is False
    assert detector.should_write("melt_pressure", 12) is False


def test_status_and_history_unaffected_by_cooldown():
    """Persisting findings stay in status/history even when writes are skipped."""
    import asyncio
    from unittest.mock import AsyncMock

    detector = _detector_with_process_water()
    detector._writer.write_finding = AsyncMock(return_value=True)
    vector = _process_water_vector(66.0)

    async def _run() -> None:
        # Scoring ticks at predict_every_n_polls=3; cooldown=18 so only the
        # first tick writes, later ticks still update status/history.
        for poll in (3, 6, 9, 12):
            await detector.on_tick(vector, "startup", False, poll)
            status = detector.get_status()
            assert status["findings_count"] > 0
            names = {f["group_name"] for f in status["findings"]}
            assert "process_water_temp_alarm" in names

    asyncio.run(_run())

    history = detector.get_history()
    assert len(history) == 4
    assert all(h["findings_count"] > 0 for h in history)
    # First scoring tick writes both alarm + critical; later ticks skip writes.
    assert history[0]["written_count"] == 2
    assert all(h["written_count"] == 0 for h in history[1:])
    assert detector._writer.write_finding.await_count == 2
