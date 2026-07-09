"""Unit tests for the phase-aware rolling baseline (Section 7.2)."""

from anomaly.baseline_tracker import BaselineTracker


def test_no_score_before_any_history():
    tracker = BaselineTracker()
    assert tracker.score("stable_production", "feeders", "15min", "mean_of_lasts", 100.0) is None
    assert tracker.sample_count("stable_production", "feeders", "15min", "mean_of_lasts") == 0


def test_score_reflects_deviation_from_baseline():
    tracker = BaselineTracker()
    # Small realistic spread so MAD isn't degenerate (zero).
    values = [100 + (i % 5 - 2) for i in range(30)]
    for v in values:
        tracker.update("stable_production", "feeders", "15min", "mean_of_lasts", v)

    z_normal = tracker.score("stable_production", "feeders", "15min", "mean_of_lasts", 101.0)
    z_outlier = tracker.score("stable_production", "feeders", "15min", "mean_of_lasts", 500.0)

    assert z_normal is not None
    assert z_outlier is not None
    assert abs(z_normal) < abs(z_outlier)


def test_phases_are_isolated():
    tracker = BaselineTracker()
    for v in [100.0] * 30:
        tracker.update("stable_production", "feeders", "15min", "mean_of_lasts", v)

    # "startup" has never been observed for this key, even though the
    # group/window/feature is identical — baselines are phase-specific.
    assert tracker.sample_count("startup", "feeders", "15min", "mean_of_lasts") == 0
    assert tracker.score("startup", "feeders", "15min", "mean_of_lasts", 100.0) is None


def test_history_capped_at_configured_size():
    tracker = BaselineTracker(history_size=10)
    for v in range(50):
        tracker.update("stable_production", "grp", "1min", "mean_of_means", float(v))
    assert tracker.sample_count("stable_production", "grp", "1min", "mean_of_means") == 10


def test_update_ignores_none_value():
    tracker = BaselineTracker()
    tracker.update("stable_production", "grp", "1min", "mean_of_means", None)
    assert tracker.sample_count("stable_production", "grp", "1min", "mean_of_means") == 0


def test_baseline_summary_reports_median_mad_n():
    tracker = BaselineTracker()
    for v in [10.0, 12.0, 10.0, 12.0]:
        tracker.update("stable_production", "grp", "1min", "mean_of_means", v)
    summary = tracker.baseline_summary("stable_production", "grp", "1min", "mean_of_means")
    assert summary["n"] == 4
    assert "median" in summary and "mad" in summary
