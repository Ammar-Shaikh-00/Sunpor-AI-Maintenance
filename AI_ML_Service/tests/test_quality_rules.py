"""Unit tests for the data-quality evaluator."""

from core.quality_rules import (
    BAD,
    GOOD,
    MISSING,
    OUT_OF_RANGE,
    SIGNAL_GROUP_ROLE_BOUNDS,
    SIGNAL_ROLE_BOUNDS,
    STALE,
    QualityEvaluator,
)


def _id_for_group(catalog: list[dict], group: str) -> int:
    return next(s["id"] for s in catalog if s["signal_group"] == group)


def test_bounds_tables_populated():
    # Role-only bounds must cover the roles that need protection everywhere.
    assert "control_output" in SIGNAL_ROLE_BOUNDS
    assert "error" in SIGNAL_ROLE_BOUNDS
    assert "status" in SIGNAL_ROLE_BOUNDS
    # Combined (group, role) bounds must cover the real production groups.
    assert ("heating_zones", "actual") in SIGNAL_GROUP_ROLE_BOUNDS
    assert ("feeders", "actual") in SIGNAL_GROUP_ROLE_BOUNDS
    assert ("melt_pressure", "actual") in SIGNAL_GROUP_ROLE_BOUNDS


def test_good_value(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "heating_zones")
    # heating_zones+actual bounds (0, 350); 230 sits inside.
    assert evaluator.evaluate(sid, 230.0) == GOOD


def test_control_output_negative_is_good():
    # PID control output at -100 must be treated as normal regardless of group.
    catalog = [
        {
            "id": 1,
            "signal_group": "heating_zones",
            "signal_role": "control_output",
            "factor": 1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    assert evaluator.evaluate(1, -100.0) == GOOD


def test_control_output_extreme_negative_out_of_range():
    catalog = [
        {
            "id": 1,
            "signal_group": "heating_zones",
            "signal_role": "control_output",
            "factor": 1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # Role bounds are (-110, 110); anything past that is genuinely OOR.
    assert evaluator.evaluate(1, -500.0) == OUT_OF_RANGE


def test_feeder_actual_out_of_range():
    catalog = [
        {"id": 1, "signal_group": "feeders", "signal_role": "actual", "factor": 1}
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # feeders+actual bounds (0, 20000); 25000 is above.
    assert evaluator.evaluate(1, 25000.0) == OUT_OF_RANGE


def test_heating_actual_normal():
    catalog = [
        {
            "id": 1,
            "signal_group": "heating_zones",
            "signal_role": "actual",
            "factor": 1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    assert evaluator.evaluate(1, 115.0) == GOOD


def test_status_out_of_range():
    catalog = [
        {"id": 1, "signal_group": "status", "signal_role": "status", "factor": 1}
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # status role bounds (0, 1); 5.0 is out.
    assert evaluator.evaluate(1, 5.0) == OUT_OF_RANGE


def test_actual_negative_flagged_for_measurement_role(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "feeders")
    # feeders+actual bounds start at 0 -> negative is OOR.
    assert evaluator.evaluate(sid, -1.0) == OUT_OF_RANGE


def test_missing_bounds_returns_good():
    # No entry in SIGNAL_ROLE_BOUNDS or SIGNAL_GROUP_ROLE_BOUNDS for this pair.
    catalog = [
        {
            "id": 1,
            "signal_group": "some_unmapped_group",
            "signal_role": "some_unmapped_role",
            "factor": 1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # No bounds means we cannot judge; the value passes as GOOD.
    assert evaluator.evaluate(1, 987654.0) == GOOD


def test_stale_after_threshold(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=3)
    sid = _id_for_group(mock_catalog, "melt_pressure")
    assert evaluator.evaluate(sid, 100.0) == GOOD  # count 1
    assert evaluator.evaluate(sid, 100.0) == GOOD  # count 2
    assert evaluator.evaluate(sid, 100.0) == STALE  # count 3 -> stale


def test_stale_resets_on_change(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=2)
    sid = _id_for_group(mock_catalog, "granulator")
    assert evaluator.evaluate(sid, 10.0) == GOOD
    assert evaluator.evaluate(sid, 10.0) == STALE
    assert evaluator.evaluate(sid, 20.0) == GOOD


def test_out_of_range_takes_priority_over_stale():
    catalog = [
        {"id": 1, "signal_group": "status", "signal_role": "status", "factor": 1}
    ]
    evaluator = QualityEvaluator(catalog, stale_count=2)
    # Value 999 is repeatedly the same (stale-eligible) AND out of (0, 1).
    assert evaluator.evaluate(1, 999.0) == OUT_OF_RANGE
    assert evaluator.evaluate(1, 999.0) == OUT_OF_RANGE


def test_mark_missing_resets_tracker(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=2)
    sid = _id_for_group(mock_catalog, "process_water")
    assert evaluator.evaluate(sid, 5.0) == GOOD
    assert evaluator.mark_missing(sid) == MISSING
    # After missing, the counter restarts -> not immediately stale.
    assert evaluator.evaluate(sid, 5.0) == GOOD


def test_bad_tag_constant_value():
    # The BAD tag is reserved for an explicit source flag (future WinCC bit).
    assert BAD == "BAD"


def test_granulator_raw_scale_is_good():
    catalog = [
        {
            "id": 1,
            "signal_group": "granulator",
            "signal_role": "actual",
            "factor": 0.1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # raw=10145 × 0.1 = 1014.5, within (0, 2000).
    assert evaluator.evaluate(1, 10145.0) == GOOD


def test_process_water_raw_scale_is_good():
    catalog = [
        {
            "id": 1,
            "signal_group": "process_water",
            "signal_role": "actual",
            "factor": 0.1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # raw=597 × 0.1 = 59.7, within (0, 200).
    assert evaluator.evaluate(1, 597.0) == GOOD


def test_screen_changer_raw_scale_is_good():
    catalog = [
        {
            "id": 1,
            "signal_group": "screen_changer",
            "signal_role": "actual",
            "factor": 0.1,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # raw=1303 × 0.1 = 130.3, within (0, 400).
    assert evaluator.evaluate(1, 1303.0) == GOOD


def test_setpoint_never_stale():
    catalog = [
        {
            "id": 1,
            "signal_group": "feeders",
            "signal_role": "setpoint",
            "factor": 1.0,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    results = [evaluator.evaluate(1, 100.0) for _ in range(10)]
    assert all(r == GOOD for r in results)


def test_actual_goes_stale():
    catalog = [
        {
            "id": 1,
            "signal_group": "feeders",
            "signal_role": "actual",
            "factor": 1.0,
        }
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    results = [evaluator.evaluate(1, 100.0) for _ in range(5)]
    assert results[-1] == STALE
