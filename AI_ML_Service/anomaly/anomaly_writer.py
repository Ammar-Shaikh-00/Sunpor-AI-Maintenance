"""Anomaly prediction writer (Section 7.2 / Section 8).

Writes each Early Anomaly Detection finding to POST /ml-predictions with a
single, constant ``prediction_type`` (read from the finding itself, which
the detector always sets to ``"anomaly_score"``). Early Anomaly is one
capability, not a stand-in for the specific risk detections that will be
built in Phase 3 (Material Behavior, Granulator/Knife, Nozzle/Screen).

Deliberately self-contained (its own run-id cache, own ``_utcnow``/
``_iso_z`` helpers) so an anomaly-write failure can never affect Process
State's prediction writes, mirroring ``state/prediction_writer.py``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RUN_CACHE_TTL_SEC = 60
RUNNING_STATUS = "RUNNING"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(dt: datetime) -> str:
    """ISO timestamp with a trailing Z (backend expects UTC)."""
    return dt.replace(tzinfo=None).isoformat() + "Z"


class AnomalyWriter:
    """Writes anomaly_score predictions tied to the active production run."""

    def __init__(
        self, signal_client, auth_client, model_name: str = "anomaly_baseline_zscore_v1"
    ) -> None:
        self._signal_client = signal_client
        self._auth_client = auth_client
        self._model_name = model_name
        self._cached_run_id = None
        self._cache_time = None

    async def get_active_run_id(self):
        """Return the id of a RUNNING production run, cached for 60s."""
        now = _utcnow()
        if (
            self._cache_time is not None
            and (now - self._cache_time).total_seconds() < RUN_CACHE_TTL_SEC
        ):
            return self._cached_run_id

        run_id = None
        try:
            runs = await self._signal_client.fetch_production_runs(limit=100)
            for run in runs:
                if str(run.get("status")) == RUNNING_STATUS:
                    run_id = run.get("id")
                    break
        except Exception as exc:
            logger.error("Failed to fetch production runs: %s", exc)
            return self._cached_run_id

        self._cached_run_id = run_id
        self._cache_time = now
        return run_id

    async def write_finding(self, finding, vector) -> bool:
        """Write one anomaly finding; return True on success (201)."""
        run_id = await self.get_active_run_id()
        if run_id is None:
            logger.warning("No RUNNING production run; skipping anomaly write")
            return False

        wf = vector.windows.get(finding.window_key) if vector else None
        window_start = wf.window_start if wf and wf.window_start else _utcnow()
        window_end = wf.window_end if wf and wf.window_end else _utcnow()

        payload = {
            "timestamp": _iso_z(_utcnow()),
            "production_run_id": run_id,
            "model_name": self._model_name,
            "prediction_type": finding.prediction_type,  # always "anomaly_score"
            "prediction_value": finding.score,
            "confidence": finding.confidence,
            "input_window_start": _iso_z(window_start),
            "input_window_end": _iso_z(window_end),
            "explanation": finding.explanation,
        }

        try:
            resp = await self._signal_client.post_ml_prediction(payload)
        except Exception as exc:
            logger.error("Failed to write anomaly ml-prediction: %s", exc)
            return False

        if resp.status_code in (200, 201):
            return True
        logger.warning("anomaly ml-prediction write returned %s", resp.status_code)
        return False
