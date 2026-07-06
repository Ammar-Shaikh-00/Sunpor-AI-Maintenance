"""Tests for the rule engine and group aggregator.

All tests load the real state/rules_config.yaml so threshold changes are
exercised by the suite.
"""

import os

from features.models import FeatureVector, SignalFeatures, WindowFeatures
from state.group_aggregator import GroupAggregator
from state.rule_engine import RuleEngine

RULES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "state", "rules_config.yaml"
)


def _engine() -> RuleEngine:
    return RuleEngine(RULES_PATH)


def test_stable_production_confirmed_from_real_data():
    group_features = {
        "status__mean_of_lasts": 1.0,
        "feeders__mean_of_lasts": 365.0,
        "feeders__mean_of_stds": 10.0,
        "extruder_meltpump__mean_of_lasts": 49.0,
        "melt_pressure__mean_of_lasts": 100.0,
        "granulator__mean_of_lasts": 323.0,
        "heating_zones__mean_of_stds": 0.1,
    }
    result = _engine().evaluate(group_features)
    assert result.phase_name == "stable_production"
    assert result.is_confirmed_phase is True
    assert result.confidence >= 0.7


def test_fault_highest_priority():
    # fault_disturbance now reads hard_fault_ratio (OOR + BAD only).
    group_features = {
        "heating_zones__hard_fault_ratio": 0.5,
        "feeders__hard_fault_ratio": 0.4,
        "extruder_meltpump__hard_fault_ratio": 0.4,
    }
    result = _engine().evaluate(group_features)
    assert result.phase_name == "fault_disturbance"


def test_stale_signals_do_not_trigger_fault():
    # All hard_fault_ratios zero -> STALE noise on bad_quality_ratio must
    # NOT be enough to fire fault_disturbance.
    group_features = {
        "heating_zones__hard_fault_ratio": 0.0,
        "feeders__hard_fault_ratio": 0.0,
        "extruder_meltpump__hard_fault_ratio": 0.0,
        "melt_pressure__mean_of_stds": 5.0,
        # Legacy bad_quality_ratio is still emitted but ignored by fault rule.
        "heating_zones__bad_quality_ratio": 0.8,
        "feeders__bad_quality_ratio": 0.8,
        "extruder_meltpump__bad_quality_ratio": 0.8,
    }
    result = _engine().evaluate(group_features)
    assert result.phase_name != "fault_disturbance"


def test_fallback_when_no_match():
    result = _engine().evaluate({})
    assert result.is_fallback is True
    assert result.phase_name == "shutdown"


def test_estimated_phase_flagged():
    group_features = {
        "heating_zones__mean_of_trends": 0.05,
        "feeders__mean_of_lasts": 10.0,
        "extruder_meltpump__mean_of_lasts": 5.0,
        "melt_pressure__mean_of_lasts": 10.0,
        "status__mean_of_lasts": 0.0,
    }
    result = _engine().evaluate(group_features)
    assert result.phase_name == "heating_up"
    assert result.is_confirmed_phase is False


def test_unknown_operator_returns_false():
    engine = _engine()
    assert engine.apply_operator(5, "nonsense", 3) is False
    assert engine.apply_operator(5, "gt", 3) is True


def test_confirmed_and_estimated_lists():
    engine = _engine()
    assert engine.confirmed_phases == ["stable_production"]
    assert "heating_up" in engine.estimated_phases
    assert "stable_production" not in engine.estimated_phases


def _sf(signal_id, group, last_val, has_bad_quality=False, has_hard_fault=False):
    return SignalFeatures(
        signal_id=signal_id,
        signal_group=group,
        mean=last_val,
        std=0.0,
        trend=0.0,
        roc=0.0,
        min_val=last_val,
        max_val=last_val,
        last_val=last_val,
        sample_count=10,
        has_bad_quality=has_bad_quality,
        has_hard_fault=has_hard_fault,
    )


def _vector_with_signals(signal_map: dict) -> FeatureVector:
    """Build a FeatureVector with a single '5min' window over ``signal_map``."""
    wf = WindowFeatures(
        window_key="5min",
        sample_count=30,
        signal_features=signal_map,
        is_ready=True,
        ready_ratio=1.0,
    )
    return FeatureVector(
        model_key="process_state",
        timestamp=__import__("datetime").datetime.now(),
        windows={"5min": wf},
        is_ready=True,
    )


def test_group_aggregator_real_values():
    # 4 extruder_meltpump signals matching real data: 120, 46, 17, 11.
    catalog = [
        {"id": 1, "signal_group": "extruder_meltpump"},
        {"id": 2, "signal_group": "extruder_meltpump"},
        {"id": 3, "signal_group": "extruder_meltpump"},
        {"id": 4, "signal_group": "extruder_meltpump"},
    ]
    agg = GroupAggregator(catalog)
    vector = _vector_with_signals(
        {
            1: _sf(1, "extruder_meltpump", 120.0),
            2: _sf(2, "extruder_meltpump", 46.0),
            3: _sf(3, "extruder_meltpump", 17.0),
            4: _sf(4, "extruder_meltpump", 11.0),
        }
    )
    out = agg.aggregate(vector, window_key="5min")
    # mean of lasts = (120 + 46 + 17 + 11) / 4 = 48.5
    assert abs(out["extruder_meltpump__mean_of_lasts"] - 48.5) < 1.0
    assert out["extruder_meltpump__bad_quality_ratio"] == 0.0


def test_group_aggregator_returns_empty_for_missing_window():
    catalog = [{"id": 1, "signal_group": "feeders"}]
    agg = GroupAggregator(catalog)
    vector = _vector_with_signals({1: _sf(1, "feeders", 100.0)})
    # No '15min' window in the fixture -> aggregator returns {} without raising.
    assert agg.aggregate(vector, window_key="15min") == {}


def test_hard_fault_ratio_excludes_stale():
    # 3 signals in a group:
    #   A: STALE only     -> bad_quality yes, hard_fault no
    #   B: OUT_OF_RANGE   -> bad_quality yes, hard_fault yes
    #   C: fully GOOD     -> neither
    catalog = [
        {"id": 1, "signal_group": "grp"},
        {"id": 2, "signal_group": "grp"},
        {"id": 3, "signal_group": "grp"},
    ]
    agg = GroupAggregator(catalog)
    vector = _vector_with_signals(
        {
            1: _sf(1, "grp", 10.0, has_bad_quality=True, has_hard_fault=False),
            2: _sf(2, "grp", 20.0, has_bad_quality=True, has_hard_fault=True),
            3: _sf(3, "grp", 30.0, has_bad_quality=False, has_hard_fault=False),
        }
    )
    out = agg.aggregate(vector, window_key="5min")
    assert abs(out["grp__bad_quality_ratio"] - (2 / 3)) < 0.01
    assert abs(out["grp__hard_fault_ratio"] - (1 / 3)) < 0.01
