"""Unit tests for detector, RunManager, and multi-line orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend_client import LineTarget
from orchestrator import ProductionOrchestrator
from production_detector import evaluate_production_active, filter_catalog_for_line
from run_manager import RunManager, RunState


def _pc_config(**overrides) -> dict:
    cfg = {
        "start_debounce_ticks": 3,
        "stop_debounce_ticks": 5,
        "is_trial": False,
        "adopt_existing_run_on_startup": True,
        "auto_run_comment": "Automatisch aus Sensoren erkannt — wartet auf Bestätigung durch den Bediener",
        "topology_refresh_sec": 300,
        "only_active_lines": True,
        "skip_lines_without_signals": True,
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


def _cached_ids(line_id: int = 10) -> dict:
    return {
        "company_id": 1,
        "company_name": "Sunpor",
        "production_line_id": line_id,
        "production_line_name": "Extrusion E10",
        "operator_id": 4,
        "default_material_type_id": 2,
    }


def _manager(backend=None, line_id: int = 10, **cfg_overrides) -> RunManager:
    client = backend or AsyncMock()
    return RunManager(client, _pc_config(**cfg_overrides), _cached_ids(line_id))


def _idle_backend(**extra) -> AsyncMock:
    backend = AsyncMock()
    backend.get_active_run = AsyncMock(return_value=None)
    backend.get_production_run = AsyncMock(return_value=None)
    for key, value in extra.items():
        setattr(backend, key, value)
    return backend


def _running_backend(run_id: int = 42, line_id: int = 10, **extra) -> AsyncMock:
    run = {"id": run_id, "status": "RUNNING", "production_line_id": line_id}
    backend = AsyncMock()
    backend.get_active_run = AsyncMock(return_value=run)
    backend.get_production_run = AsyncMock(return_value=run)
    for key, value in extra.items():
        setattr(backend, key, value)
    return backend


def _catalog_two_lines() -> list[dict]:
    """Line 10 has producing signals; line 20 has idle/low signals."""
    return [
        {"id": 1, "production_line_id": 10, "signal_group": "status", "signal_role": "status", "active": True},
        {"id": 2, "production_line_id": 10, "signal_group": "feeders", "signal_role": "actual", "active": True},
        {"id": 3, "production_line_id": 10, "signal_group": "extruder_meltpump", "signal_role": "actual", "active": True},
        {"id": 4, "production_line_id": 10, "signal_group": "melt_pressure", "signal_role": "actual", "active": True},
        {"id": 11, "production_line_id": 20, "signal_group": "status", "signal_role": "status", "active": True},
        {"id": 12, "production_line_id": 20, "signal_group": "feeders", "signal_role": "actual", "active": True},
        {"id": 13, "production_line_id": 20, "signal_group": "extruder_meltpump", "signal_role": "actual", "active": True},
        {"id": 14, "production_line_id": 20, "signal_group": "melt_pressure", "signal_role": "actual", "active": True},
    ]


def _latest_mixed() -> list[dict]:
    vals = {
        1: 1.0,
        2: 100.0,
        3: 40.0,
        4: 90.0,
        11: 0.0,
        12: 5.0,
        13: 2.0,
        14: 10.0,
    }
    return [
        {"signal_id": sid, "value_scaled": val, "quality": "GOOD"}
        for sid, val in vals.items()
    ]


# ── Detector ──────────────────────────────────────────────────────────


def test_filter_catalog_for_line():
    filtered = filter_catalog_for_line(_catalog_two_lines(), 10)
    assert len(filtered) == 4
    assert all(int(r["production_line_id"]) == 10 for r in filtered)


def test_detector_scopes_to_production_line():
    catalog = _catalog_two_lines()
    latest = _latest_mixed()
    active_10, info_10 = evaluate_production_active(
        catalog, latest, _pc_config(), production_line_id=10
    )
    active_20, info_20 = evaluate_production_active(
        catalog, latest, _pc_config(), production_line_id=20
    )
    assert active_10 is True
    assert info_10["passed"] == 4
    assert active_20 is False
    assert info_20["passed"] < 4


def test_detector_no_signals_for_line():
    active, info = evaluate_production_active(
        _catalog_two_lines(),
        _latest_mixed(),
        _pc_config(),
        production_line_id=999,
    )
    assert active is False
    assert info["reason"] == "no_signals_for_line"


# ── RunManager ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_no_run_before_start_debounce():
    backend = _idle_backend(
        is_production_active=AsyncMock(
            return_value=(True, {"passed": 4, "evaluated": 4})
        ),
        create_production_run=AsyncMock(),
    )
    mgr = _manager(backend, start_debounce_ticks=3)

    for _ in range(2):
        await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    backend.create_production_run.assert_not_called()
    backend.is_production_active.assert_awaited_with(10)


@pytest.mark.asyncio
async def test_creates_run_after_start_debounce():
    backend = _idle_backend(
        is_production_active=AsyncMock(
            return_value=(True, {"passed": 4, "evaluated": 4})
        ),
        resolve_current_shift_id=AsyncMock(return_value=7),
        create_production_run=AsyncMock(return_value={"id": 99}),
    )
    mgr = _manager(backend, start_debounce_ticks=3)

    for _ in range(3):
        await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 99
    assert backend.create_production_run.await_count == 1


@pytest.mark.asyncio
async def test_completes_run_after_stop_debounce():
    backend = _running_backend(
        42,
        is_production_active=AsyncMock(
            return_value=(False, {"passed": 0, "evaluated": 4})
        ),
        complete_production_run=AsyncMock(return_value={"id": 42}),
    )
    mgr = _manager(backend, stop_debounce_ticks=5)
    mgr.state = RunState.RUNNING
    mgr.active_run_id = 42

    for _ in range(5):
        await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    assert mgr.active_run_id is None
    backend.complete_production_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_adopts_running_run_each_tick():
    backend = _running_backend(
        88,
        is_production_active=AsyncMock(
            return_value=(True, {"passed": 4, "evaluated": 4})
        ),
        create_production_run=AsyncMock(),
    )
    mgr = _manager(backend)

    await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 88
    backend.create_production_run.assert_not_called()


@pytest.mark.asyncio
async def test_sync_when_run_completed_externally_goes_idle():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(
        return_value=(False, {"passed": 0, "evaluated": 4})
    )
    backend.get_active_run = AsyncMock(return_value=None)
    backend.get_production_run = AsyncMock(
        return_value={"id": 42, "status": "COMPLETED", "production_line_id": 10}
    )
    backend.complete_production_run = AsyncMock()
    mgr = _manager(backend)
    mgr.state = RunState.RUNNING
    mgr.active_run_id = 42

    await mgr.on_tick()

    assert mgr.state == RunState.IDLE
    assert mgr.active_run_id is None
    backend.complete_production_run.assert_not_called()


@pytest.mark.asyncio
async def test_after_external_complete_creates_new_run_when_sensors_active():
    backend = AsyncMock()
    backend.is_production_active = AsyncMock(
        return_value=(True, {"passed": 4, "evaluated": 4})
    )
    backend.get_active_run = AsyncMock(return_value=None)
    backend.get_production_run = AsyncMock(
        return_value={"id": 42, "status": "COMPLETED", "production_line_id": 10}
    )
    backend.resolve_current_shift_id = AsyncMock(return_value=1)
    backend.create_production_run = AsyncMock(return_value={"id": 100})
    mgr = _manager(backend, start_debounce_ticks=1)
    mgr.state = RunState.RUNNING
    mgr.active_run_id = 42

    await mgr.on_tick()

    assert mgr.state == RunState.RUNNING
    assert mgr.active_run_id == 100


# ── Orchestrator ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orchestrator_creates_manager_per_discovered_line():
    client = AsyncMock()
    client.discover_managed_lines = AsyncMock(
        return_value=[
            LineTarget(1, "Sunpor", 10, "E10", signal_count=40),
            LineTarget(1, "Sunpor", 20, "E20", signal_count=30),
            LineTarget(2, "OtherCo", 30, "LineA", signal_count=10),
        ]
    )
    client.get_active_run = AsyncMock(return_value=None)
    client.begin_poll_snapshot = AsyncMock()
    client.end_poll_snapshot = MagicMock()
    client.is_production_active = AsyncMock(
        return_value=(False, {"passed": 0, "evaluated": 4})
    )

    orch = ProductionOrchestrator(
        client, _pc_config(), operator_id=4, default_material_type_id=2
    )
    await orch.startup()

    assert orch.line_count == 3
    assert set(orch.managers) == {10, 20, 30}

    await orch.on_tick()

    client.begin_poll_snapshot.assert_awaited_once()
    assert client.is_production_active.await_count == 3
    client.end_poll_snapshot.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_isolates_line_failures():
    client = AsyncMock()
    client.discover_managed_lines = AsyncMock(
        return_value=[
            LineTarget(1, "Sunpor", 10, "E10", signal_count=4),
            LineTarget(1, "Sunpor", 20, "E20", signal_count=4),
        ]
    )
    client.get_active_run = AsyncMock(return_value=None)
    client.begin_poll_snapshot = AsyncMock()
    client.end_poll_snapshot = MagicMock()

    async def _active(line_id: int):
        if line_id == 10:
            raise RuntimeError("boom")
        return False, {"passed": 0, "evaluated": 4}

    client.is_production_active = AsyncMock(side_effect=_active)

    orch = ProductionOrchestrator(
        client, _pc_config(), operator_id=4, default_material_type_id=2
    )
    await orch.startup()
    await orch.on_tick()  # must not raise

    assert client.is_production_active.await_count == 2
    client.end_poll_snapshot.assert_called_once()
