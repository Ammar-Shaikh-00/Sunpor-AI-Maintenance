"""Unit tests for the data-quality evaluator."""

from core.quality_rules import (
    BAD,
    GOOD,
    MISSING,
    OUT_OF_RANGE,
    SIGNAL_GROUP_BOUNDS,
    STALE,
    QualityEvaluator,
)


def _id_for_group(catalog: list[dict], group: str) -> int:
    return next(s["id"] for s in catalog if s["signal_group"] == group)


def test_all_groups_have_bounds():
    # Every group used by the catalog must have configured bounds.
    expected = {
        "heating_zones",
        "feeders",
        "screen_changer",
        "process_water",
        "granulator",
        "melt_pressure",
        "offspec",
        "pentane_nitrogen",
        "extruder_meltpump",
        "status",
    }
    assert expected.issubset(SIGNAL_GROUP_BOUNDS.keys())


def test_good_value(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "heating_zones")
    assert evaluator.evaluate(sid, 230.0) == GOOD


def test_out_of_range_factor_one(mock_catalog):
    # status group bounds (0, 100), factor 1 -> raw max 100.
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "status")
    assert evaluator.evaluate(sid, 200.0) == OUT_OF_RANGE


def test_out_of_range_negative(mock_catalog):
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "feeders")
    assert evaluator.evaluate(sid, -1.0) == OUT_OF_RANGE


def test_control_output_negative_allowed():
    catalog = [
        {
            "id": 1,
            "signal_group": "heating_zones",
            "signal_role": "control_output",
            "factor": 1,
        },
        {
            "id": 2,
            "signal_group": "heating_zones",
            "signal_role": "actual",
            "factor": 1,
        },
    ]
    evaluator = QualityEvaluator(catalog, stale_count=5)
    # PID control output at -100 is normal — not flipped, not flagged.
    assert evaluator.evaluate(1, -100.0) == GOOD
    # Actual temperature must stay non-negative.
    assert evaluator.evaluate(2, -100.0) == OUT_OF_RANGE


def test_control_output_extreme_negative_still_out_of_range():
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
    assert evaluator.evaluate(1, -6000.0) == OUT_OF_RANGE


def test_range_uses_factor(mock_catalog):
    # screen_changer bounds (0, 10000), factor 0.1 -> raw max 1000.
    evaluator = QualityEvaluator(mock_catalog, stale_count=5)
    sid = _id_for_group(mock_catalog, "screen_changer")
    assert evaluator.evaluate(sid, 500.0) == GOOD
    assert evaluator.evaluate(sid, 2000.0) == OUT_OF_RANGE


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
    # A new value resets the counter.
    assert evaluator.evaluate(sid, 20.0) == GOOD


def test_out_of_range_takes_priority_over_stale(mock_catalog):
    # status bounds raw max 100; repeated 999 is both stale-eligible and OOR.
    evaluator = QualityEvaluator(mock_catalog, stale_count=2)
    sid = _id_for_group(mock_catalog, "status")
    assert evaluator.evaluate(sid, 999.0) == OUT_OF_RANGE
    assert evaluator.evaluate(sid, 999.0) == OUT_OF_RANGE


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
