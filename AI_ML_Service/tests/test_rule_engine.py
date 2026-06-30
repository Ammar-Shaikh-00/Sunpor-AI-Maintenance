"""Tests for the rule engine and group aggregator.

All tests load the real state/rules_config.yaml so threshold changes are
exercised by the suite.
"""

import os

from features.models import FeatureVector, SignalFeatures
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
    group_features = {
        "heating_zones__bad_quality_ratio": 0.5,
        "feeders__bad_quality_ratio": 0.4,
        "extruder_meltpump__bad_quality_ratio": 0.4,
    }
    result = _engine().evaluate(group_features)
    assert result.phase_name == "fault_disturbance"


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


def _sf(signal_id, group, last_val):
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
        has_bad_quality=False,
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
    vector = FeatureVector(
        model_key="process_state",
        timestamp=__import__("datetime").datetime.now(),
        signal_features={
            1: _sf(1, "extruder_meltpump", 120.0),
            2: _sf(2, "extruder_meltpump", 46.0),
            3: _sf(3, "extruder_meltpump", 17.0),
            4: _sf(4, "extruder_meltpump", 11.0),
        },
        is_ready=True,
        ready_ratio=1.0,
    )
    out = agg.aggregate(vector)
    # mean of lasts = (120 + 46 + 17 + 11) / 4 = 48.5
    assert abs(out["extruder_meltpump__mean_of_lasts"] - 48.5) < 1.0
    assert out["extruder_meltpump__bad_quality_ratio"] == 0.0
