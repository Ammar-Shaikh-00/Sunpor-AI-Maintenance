"""Tests for Low-Production Cause & Severity sub-analysis (Section 7.1)."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from types import SimpleNamespace

import yaml

from features.models import FeatureVector, SignalFeatures, WindowFeatures
from state.cause_resolver import CauseResolver
from state.low_production_analyzer import LowProductionAnalyzer
from state.low_production_models import CauseCandidate

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "state",
    "low_production_config.yaml",
)


def _catalog() -> list[dict]:
    return [
        {"id": 1, "signal_group": "feeders", "signal_role": "actual"},
        {"id": 2, "signal_group": "feeders", "signal_role": "actual"},
        {"id": 3, "signal_group": "feeders", "signal_role": "setpoint"},
        {"id": 4, "signal_group": "feeders", "signal_role": "setpoint"},
        {"id": 5, "signal_group": "feeders", "signal_role": "error"},
        {"id": 6, "signal_group": "melt_pressure", "signal_role": "actual"},
        {"id": 7, "signal_group": "extruder_meltpump", "signal_role": "actual"},
    ]


def _sf(signal_id, group, last_val, std=0.0):
    return SignalFeatures(
        signal_id=signal_id,
        signal_group=group,
        mean=last_val,
        std=std,
        trend=0.0,
        roc=0.0,
        min_val=last_val,
        max_val=last_val,
        last_val=last_val,
        sample_count=30,
        has_bad_quality=False,
        has_hard_fault=False,
    )


def _vector(signal_map: dict, windows=("5min", "15min")) -> FeatureVector:
    return FeatureVector(
        model_key="process_state",
        timestamp=datetime.now(timezone.utc),
        windows={
            w: WindowFeatures(
                window_key=w,
                sample_count=30 if w == "5min" else 90,
                signal_features=signal_map,
                is_ready=True,
                ready_ratio=1.0,
            )
            for w in windows
        },
        is_ready=True,
    )


def _throughput_map(actual: float, setpoint: float) -> dict:
    return {
        1: _sf(1, "feeders", actual),
        2: _sf(2, "feeders", actual),
        3: _sf(3, "feeders", setpoint),
        4: _sf(4, "feeders", setpoint),
        5: _sf(5, "feeders", 0.0),
        6: _sf(6, "melt_pressure", 100.0, std=1.0),
        7: _sf(7, "extruder_meltpump", 50.0, std=1.0),
    }


class FakeWriter:
    def __init__(self, run_id=1):
        self.run_id = run_id
        self.writes = []

    async def get_active_run_id(self):
        return self.run_id

    async def write_low_production(self, result, vector, run_id, window_key="5min"):
        self.writes.append(
            {
                "result": result,
                "run_id": run_id,
                "window_key": window_key,
            }
        )
        return True


class FakeSignalClient:
    def __init__(self, production_events=None, material_events=None, raise_on=None):
        self.production_events = production_events or []
        self.material_events = material_events or []
        self.raise_on = raise_on or set()

    async def get_production_events(self, run_id, lookback_minutes):
        if "production" in self.raise_on:
            raise RuntimeError("endpoint missing")
        return list(self.production_events)

    async def get_material_behavior_events(self, run_id, lookback_minutes):
        if "material" in self.raise_on:
            raise RuntimeError("endpoint missing")
        return list(self.material_events)


def _phase(name="low_production"):
    return SimpleNamespace(phase_name=name)


def _analyzer(config_overrides=None, writer=None, signal_client=None):
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if config_overrides:
        for key, value in config_overrides.items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value

    # Write a temp-like in-memory config by monkeypatching load via file rewrite
    # is avoided — instead construct analyzer then replace config.
    analyzer = LowProductionAnalyzer(
        _catalog(),
        CONFIG_PATH,
        signal_client or FakeSignalClient(),
        writer or FakeWriter(),
    )
    if config_overrides:
        analyzer._config = config
        analyzer._cause_resolver = CauseResolver(
            _catalog(), config, signal_client or FakeSignalClient()
        )
    return analyzer


def test_severity_computed_correctly():
    analyzer = _analyzer()
    severity = analyzer._compute_severity(
        _vector(_throughput_map(actual=700.0, setpoint=1000.0)), "5min"
    )
    assert severity is not None
    assert abs(severity - 0.3) < 1e-6


def test_severity_clamped_at_zero_when_above_setpoint():
    analyzer = _analyzer()
    severity = analyzer._compute_severity(
        _vector(_throughput_map(actual=1200.0, setpoint=1000.0)), "5min"
    )
    assert severity == 0.0


def test_duration_resets_on_phase_change():
    analyzer = _analyzer()
    vector = _vector(_throughput_map(700.0, 1000.0))

    asyncio.run(analyzer.on_tick(vector, _phase("stable_production"), 1, []))
    assert analyzer.duration_ticks == 0

    asyncio.run(analyzer.on_tick(vector, _phase("low_production"), 2, []))
    assert analyzer.duration_ticks == 1

    asyncio.run(analyzer.on_tick(vector, _phase("stable_production"), 3, []))
    assert analyzer.duration_ticks == 0


def test_min_duration_gate_blocks_early_write():
    writer = FakeWriter()
    analyzer = _analyzer(
        config_overrides={"duration": {"min_duration_ticks_for_alert": 3}},
        writer=writer,
    )
    vector = _vector(_throughput_map(700.0, 1000.0))

    asyncio.run(analyzer.on_tick(vector, _phase("low_production"), 1, []))
    asyncio.run(analyzer.on_tick(vector, _phase("low_production"), 2, []))
    assert writer.writes == []

    asyncio.run(analyzer.on_tick(vector, _phase("low_production"), 3, []))
    assert len(writer.writes) == 1


def test_cause_priority_planned_wins_over_others():
    signal_client = FakeSignalClient(
        production_events=[
            {"id": 11, "level_2": "Low Production", "reason": "planned slowdown"}
        ]
    )
    # Feeder error would also match if checked later.
    signal_map = _throughput_map(700.0, 1000.0)
    signal_map[5] = _sf(5, "feeders", 1.0)
    writer = FakeWriter()
    analyzer = _analyzer(writer=writer, signal_client=signal_client)

    asyncio.run(
        analyzer.on_tick(
            _vector(signal_map), _phase("low_production"), 1, []
        )
    )
    assert analyzer.last_result is not None
    assert analyzer.last_result.cause_name == "planned_slowdown"
    assert analyzer.last_result.is_planned is True


def test_cause_fallback_unknown_when_no_resolver_matches():
    writer = FakeWriter()
    analyzer = _analyzer(writer=writer, signal_client=FakeSignalClient())
    asyncio.run(
        analyzer.on_tick(
            _vector(_throughput_map(700.0, 1000.0)),
            _phase("low_production"),
            1,
            [],
        )
    )
    assert analyzer.last_result is not None
    assert analyzer.last_result.cause_name == "unknown"
    assert analyzer.last_result.confidence == 0.0


def test_feeder_fault_resolver_detects_error_signal():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    resolver = CauseResolver(_catalog(), config, FakeSignalClient())
    signal_map = _throughput_map(700.0, 1000.0)
    signal_map[5] = _sf(5, "feeders", 1.0)
    candidate = resolver._resolve_feeder_fault(
        _vector(signal_map), config["cause_resolution"]["feeder_fault"]
    )
    assert candidate is not None
    assert candidate.cause_name == "feeder_fault"
    assert isinstance(candidate, CauseCandidate)


def test_planned_slowdown_resolver_handles_missing_endpoint():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    resolver = CauseResolver(
        _catalog(),
        config,
        FakeSignalClient(raise_on={"production"}),
    )
    candidate = asyncio.run(
        resolver._resolve_planned_slowdown(
            1, config["cause_resolution"]["planned_slowdown"]
        )
    )
    assert candidate is None


def test_phase_transition_resolver_detects_recent_startup():
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    resolver = CauseResolver(_catalog(), config, FakeSignalClient())
    history = [
        {"phase_name": "startup"},
        {"phase_name": "low_production"},
    ]
    candidate = resolver._resolve_phase_transition(
        history, config["cause_resolution"]["phase_transition"]
    )
    assert candidate is not None
    assert candidate.cause_name == "phase_transition"
    assert "startup" in candidate.evidence
