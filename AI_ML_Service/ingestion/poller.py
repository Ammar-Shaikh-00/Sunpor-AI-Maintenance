"""Async ingestion poller.

Reads the latest live snapshot from the backend on a fixed interval, passes
it through the cleaning layer, and pushes only validated ``CleanRecord``s into
the in-memory rolling buffer. Read-only: this loop never writes time-series
data — it only consumes ``/signal-timeseries/latest``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from cleaning.cleaner import DataCleaner
from core.config import get_settings
from ingestion.signal_client import SignalClient
from ingestion.window_buffer import RollingWindowBuffer

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IngestionPoller:
    """Periodically polls live signals and fills the rolling window buffer."""

    LOG_EVERY = 10

    def __init__(
        self,
        catalog: list[dict],
        signal_client: SignalClient,
        cleaner: DataCleaner,
        window_buffer: RollingWindowBuffer,
        feature_engine: Optional[Any] = None,
        process_state_detector: Optional[Any] = None,
    ) -> None:
        self._catalog_map = {s["id"]: s for s in catalog if s.get("id") is not None}
        self._signal_client = signal_client
        self._cleaner = cleaner
        self._buffer = window_buffer
        self._feature_engine = feature_engine
        self._process_state_detector = process_state_detector

        self.total_polls = 0
        self.total_values = 0
        self.bad_quality_count = 0
        self.start_time = _utcnow()
        self.last_report = None
        self.last_vectors = {}

    async def poll_once(self) -> dict:
        """Fetch one snapshot, clean it, and buffer the valid readings."""
        raw_snapshot = await self._signal_client.fetch_latest()
        # All cleaning happens here — nothing else touches raw data.
        clean_records, report = self._cleaner.clean_snapshot(
            self._as_entries(raw_snapshot)
        )

        for record in clean_records:
            if not record.is_valid:
                continue
            self._buffer.push(
                record.signal_id,
                record.timestamp.isoformat(),
                record.value_scaled,
                record.quality,
            )

        self.total_polls += 1
        self.total_values += report.total_valid
        self.bad_quality_count += report.total_received - report.total_valid
        self.last_report = report

        if self._feature_engine is not None:
            self.last_vectors = self._feature_engine.on_tick(self._buffer)
            vector = self._feature_engine.get_vector("process_state")
            if self._process_state_detector is not None and vector is not None:
                await self._process_state_detector.on_tick(vector, self.total_polls)

        if self.total_polls % self.LOG_EVERY == 0:
            logger.info(
                "Poll #%d | received=%d | valid=%d | invalid=%d | "
                "missing=%d | duplicates_dropped=%d",
                self.total_polls,
                report.total_received,
                report.total_valid,
                report.total_invalid,
                len(report.missing_signals),
                report.duplicate_dropped,
            )

        return {
            "total_polls": self.total_polls,
            "signals_in_snapshot": report.total_received,
            "bad_quality_count": self.bad_quality_count,
        }

    async def run_loop(self) -> None:
        """Run forever; never crash on a single failed poll."""
        interval = get_settings().POLL_INTERVAL_SEC
        while True:
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                logger.info("Poller loop cancelled")
                raise
            except Exception as exc:
                logger.error("Poll failed: %s", exc)
            await asyncio.sleep(interval)

    def stats(self) -> dict:
        """Return runtime counters plus the current buffer snapshot."""
        uptime_sec = (_utcnow() - self.start_time).total_seconds()
        last_report = {}
        if self.last_report is not None:
            r = self.last_report
            last_report = {
                "total_received": r.total_received,
                "total_valid": r.total_valid,
                "total_invalid": r.total_invalid,
                "missing_signals_count": len(r.missing_signals),
                "duplicate_dropped": r.duplicate_dropped,
                "quality_counts": r.quality_counts,
            }
        return {
            "total_polls": self.total_polls,
            "total_values": self.total_values,
            "bad_quality_count": self.bad_quality_count,
            "uptime_sec": round(uptime_sec, 1),
            "buffer_snapshot": self._buffer.snapshot(),
            "last_cleaning_report": last_report,
        }

    def last_report_dict(self) -> dict:
        """Full CleaningReport as a dict (for the cleaning-report endpoint)."""
        if self.last_report is None:
            return {"status": "no_data_yet"}
        data = asdict(self.last_report)
        data["timestamp"] = self.last_report.timestamp.isoformat()
        return data

    @staticmethod
    def _as_entries(snapshot: Any) -> list[dict]:
        """Normalize a list-or-paginated snapshot into a plain list of entries."""
        if isinstance(snapshot, list):
            return snapshot
        if isinstance(snapshot, dict):
            for key in ("items", "results", "data", "values"):
                value = snapshot.get(key)
                if isinstance(value, list):
                    return value
        return []
