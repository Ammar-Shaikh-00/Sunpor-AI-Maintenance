"""Unit tests for RunManager + sensor production detector."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from production_detector import evaluate_production_active
from run_manager import RunManager, RunState


def _pc_config(**overrides) -> dict:
    cfg = {
        "start_debounce_ticks": 3,
        "stop_debounce_ticks": 5,
        "is_trial": False,
        "adopt_existing_run_on_startup": True,
        "auto_run_comment": "Auto-detected from sensors",
        "production_active": {
            "min_conditions_ratio": 1.0,
            "require_good_quality": True,
            "conditions": [
                {"group": "status", "role": None, "operator": "gte", "threshold": 1.0},
                {
                    "group": "feeders",
                    "role": "actual",
                    "operator": "gte",
                    "threshold": 50.0,
                },
                {
                    "group": "extruder_meltpump",
                    "role": "actual",
                    "operator": "gte",
                    "threshold": 15.0,
                },
                {
                    "group": "melt_pressure",
                    "role": "actual",
                    "operator": "gte",
                    "threshold": 40.0,
                },
            ],
        },
    }
    cfg.update(overrides)
    return cfg


def _cached_ids() -> dict:
    return {
        "company_id": 1,
        "production_line_id": 10,
        "operator_id": 4,
        "default_material_type_id": 2,
    }


def _manager(backend=None, **cfg_overrides) -> RunManager:
    client = backend or AsyncMock()
    return RunManager(client, _pc_config(**cfg_overrides), _cached_ids())


def _catalog() -> list[dict]:
    return [
        {"id": 1, "signal_group": "status", "signal_role": "status"},
        {"id": 2, "signal_group": "feeders", "signal_role": "actual"},
        {"id": 3, "signal_group": "feeders", "signal_role": "setpoint"},
        {"id": 4, "signal_group": "extruder_meltpump", "signal_role": "actual"},
        {"id": 5, "signal_group": "melt_pressure", "signal_role": "actual"},
    ]


def _latest(overrides: dict[int, float] | None = None) -> list[dict]:
    defaults = {
        1: 1.0,
        2: 100.0,
        3: 100.0,
        4: 40.0,
        5: 90.0,
    }
    if overrides:
        defaults.update(overrides)
    return [
        {
            "signal_id": sid,
            "value_scaled": val,
            "value_raw": val,
            "quality": "GOOD",
        }
        for sid, val in defaults.items()
    ]


# ── Detector unit tests ───────────────────────────────────────────────


def test_detector_active_when_all_conditions_pass():
    active, info = evaluate_production_active(_catalog(), _latest(), _pc_config())
    assert active is True
    assert info["passed"] == 4


def test_detector_inactive_when_feeders_low():
    active, info = evaluate_production_active(
        _catalog(), _latest({2: 10.0}), _pc_config()
    )
    assert active is False
    feeder = next(d for d in info["details"] if d["group"] == "feeders")
    assert feeder["passed"] is False


def test_detector_ignores_setpoint_for_feeders_role_actual():
    # Only setpoint high, actual low → fail feeders condition
    latest = _latest({2: 5.0, 3: 500.0})
    active, info = evaluate_production_active(_catalog(), latest, _pc_config())
    assert active is False


# ── RunManager debounce / adopt tests ─────────────────────────────────


@pytest.mark.asyncio
async def test_no_run_before_start_debounce():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(return_value=(True, {"passed": 4, "evaluated": 4}))
    backend.create_production_run = AsyncMock()
    mgr = _manager(backend, start_debounce_ticks=3)

    for _ in range(2):
        await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    backend.create_production_run.assert_not_called()


@pytest.mark.asyncio
async def test_creates_run_after_start_debounce():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(return_value=(True, {"passed": 4, "evaluated": 4}))
    backend.resolve_current_shift_id = AsyncMock(return_value=7)
    backend.create_production_run = AsyncMock(return_value={"id": 99})
    mgr = _manager(backend, start_debounce_ticks=3)

    for _ in range(3):
        await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 99
    assert backend.create_production_run.await_count == 1
    kwargs = backend.create_production_run.await_args.kwargs
    assert kwargs.get("comment") == "Auto-detected from sensors"


@pytest.mark.asyncio
async def test_no_complete_before_stop_debounce():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(
        return_value=(False, {"passed": 0, "evaluated": 4})
    )
    backend.complete_production_run = AsyncMock()
    mgr = _manager(backend, stop_debounce_ticks=5)
    mgr.state = RunState.RUNNING
    mgr.active_run_id = 42

    for _ in range(4):
        await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    backend.complete_production_run.assert_not_called()


@pytest.mark.asyncio
async def test_completes_run_after_stop_debounce():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(
        return_value=(False, {"passed": 0, "evaluated": 4})
    )
    backend.complete_production_run = AsyncMock(return_value={"id": 42})
    mgr = _manager(backend, stop_debounce_ticks=5)
    mgr.state = RunState.RUNNING
    mgr.active_run_id = 42

    for _ in range(5):
        await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    assert mgr.active_run_id is None
    backend.complete_production_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_adopts_existing_run_on_startup():
    backend = AsyncMock()
    backend.fetch_catalog = AsyncMock(return_value=[])
    backend.get_active_run = AsyncMock(return_value={"id": 55, "status": "RUNNING"})
    backend.create_production_run = AsyncMock()
    mgr = _manager(backend)

    await mgr.startup()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 55
    backend.create_production_run.assert_not_called()


@pytest.mark.asyncio
async def test_no_duplicate_run_on_400_conflict():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(return_value=(True, {"passed": 4, "evaluated": 4}))
    backend.resolve_current_shift_id = AsyncMock(return_value=1)
    backend.create_production_run = AsyncMock(return_value=None)
    backend.get_active_run = AsyncMock(
        return_value={"id": 77, "status": "RUNNING", "production_line_id": 10}
    )
    mgr = _manager(backend, start_debounce_ticks=1)

    await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 77


@pytest.mark.asyncio
async def test_no_signals_yet_stays_idle():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(
        return_value=(False, {"reason": "no_latest_signals"})
    )
    backend.create_production_run = AsyncMock()
    mgr = _manager(backend)

    await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    backend.create_production_run.assert_not_called()
