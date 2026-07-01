"""Unit tests for the ingestion poller (no network — fake signal client)."""

import asyncio
from datetime import datetime, timezone

from cleaning.cleaner import DataCleaner
from core.quality_rules import QualityEvaluator
from ingestion.poller import IngestionPoller
from ingestion.window_buffer import RollingWindowBuffer


class FakeSignalClient:
    """Returns a fixed snapshot; records how many times it was called."""

    def __init__(self, snapshot: list[dict]) -> None:
        self._snapshot = snapshot
        self.calls = 0

    async def fetch_latest(self):
        self.calls += 1
        return self._snapshot


def _catalog(n: int) -> list[dict]:
    groups = [
        "heating_zones",
        "feeders",
        "melt_pressure",
        "granulator",
        "status",
    ]
    # Roles must match the quality evaluator's new bounds tables.
    roles = ["actual", "actual", "actual", "actual", "status"]
    return [
        {
            "id": i,
            "wincc_tag": f"TAG_{i}",
            "signal_group": groups[i - 1],
            "signal_role": roles[i - 1],
            "factor": 1,
        }
        for i in range(1, n + 1)
    ]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _snapshot(n: int) -> list[dict]:
    ts = _now_iso()
    return [
        {
            "signal_id": i,
            "wincc_tag": f"TAG_{i}",
            "value_raw": 10.0 + i,
            "value_scaled": 10.0 + i,
            "quality": "GOOD",
            "timestamp": ts,
            "source": "WINCC_POLL",
        }
        for i in range(1, n + 1)
    ]


def _build(catalog, snapshot):
    client = FakeSignalClient(snapshot)
    evaluator = QualityEvaluator(catalog, stale_count=5)
    cleaner = DataCleaner(catalog, evaluator)
    buffer = RollingWindowBuffer([s["id"] for s in catalog], max_samples=30)
    poller = IngestionPoller(catalog, client, cleaner, buffer)
    return poller, buffer


def test_poll_once_fills_buffer():
    poller, buffer = _build(_catalog(5), _snapshot(5))

    result = asyncio.run(poller.poll_once())

    assert result["signals_in_snapshot"] == 5
    assert result["total_polls"] == 1
    # One entry buffered per signal.
    assert buffer.snapshot() == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}


def test_stats_after_one_poll():
    poller, _ = _build(_catalog(5), _snapshot(5))

    asyncio.run(poller.poll_once())
    stats = poller.stats()

    assert stats["total_polls"] == 1
    assert stats["total_values"] == 5
    assert stats["bad_quality_count"] == 0
    assert "uptime_sec" in stats
    assert stats["buffer_snapshot"] == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
    assert stats["last_cleaning_report"]["total_received"] == 5


def test_out_of_range_quality_preserved_in_buffer():
    catalog = _catalog(5)
    snapshot = _snapshot(5)
    # Signal 5 has role=status, bounds (0, 1). 999 forces OUT_OF_RANGE,
    # but the record is still valid and buffered with that quality tag.
    snapshot[4]["value_raw"] = 999.0
    snapshot[4]["value_scaled"] = 999.0
    poller, buffer = _build(catalog, snapshot)

    asyncio.run(poller.poll_once())

    assert buffer.get_latest(5)["quality"] == "OUT_OF_RANGE"
    # All five are still valid (quality flag does not invalidate).
    assert poller.bad_quality_count == 0


def test_invalid_record_counts_as_bad():
    catalog = _catalog(5)
    snapshot = _snapshot(5)
    # Type error on signal 2 -> invalid -> excluded from buffer, counted bad.
    snapshot[1]["value_raw"] = "not_a_float"
    poller, buffer = _build(catalog, snapshot)

    asyncio.run(poller.poll_once())

    assert poller.bad_quality_count == 1
    assert buffer.snapshot()[2] == 0  # signal 2 not buffered


def test_missing_signal_excluded_from_buffer():
    catalog = _catalog(5)
    snapshot = _snapshot(4)  # signal 5 missing from snapshot
    poller, buffer = _build(catalog, snapshot)

    asyncio.run(poller.poll_once())

    assert poller.last_report.missing_signals == [5]
    assert buffer.snapshot()[5] == 0  # missing record not buffered


def test_feature_engine_on_tick_called():
    catalog = _catalog(5)
    client = FakeSignalClient(_snapshot(5))
    evaluator = QualityEvaluator(catalog, stale_count=5)
    cleaner = DataCleaner(catalog, evaluator)
    buffer = RollingWindowBuffer([s["id"] for s in catalog], max_samples=30)

    class FakeEngine:
        def __init__(self):
            self.ticks = 0

        def on_tick(self, buf):
            self.ticks += 1
            return {}

        def get_vector(self, model_key):
            return None

    engine = FakeEngine()
    poller = IngestionPoller(catalog, client, cleaner, buffer, feature_engine=engine)

    asyncio.run(poller.poll_once())
    assert engine.ticks == 1
