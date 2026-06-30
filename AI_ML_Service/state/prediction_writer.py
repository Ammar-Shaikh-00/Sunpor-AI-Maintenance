"""Prediction writer.

Resolves the active (RUNNING) production run and writes process-state
predictions to POST /ml-predictions. The active run id is cached briefly to
avoid querying the backend on every prediction.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

MODEL_NAME = "process_state_rule_v1"
PREDICTION_TYPE = "process_state"
RUN_CACHE_TTL_SEC = 60
RUNNING_STATUS = "RUNNING"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_z(dt: datetime) -> str:
    """ISO timestamp with a trailing Z (backend expects UTC)."""
    return dt.replace(tzinfo=None).isoformat() + "Z"


class PredictionWriter:
    """Writes process-state predictions tied to the active production run."""

    def __init__(self, signal_client, auth_client) -> None:
        self._signal_client = signal_client
        self._auth_client = auth_client
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

    async def write_prediction(self, result, vector) -> bool:
        """Write one prediction; return True on success (201)."""
        run_id = await self.get_active_run_id()
        if run_id is None:
            logger.warning("No RUNNING production run; skipping prediction write")
            return False

        payload = {
            "timestamp": _iso_z(_utcnow()),
            "production_run_id": run_id,
            "model_name": MODEL_NAME,
            "prediction_type": PREDICTION_TYPE,
            "prediction_value": float(result.phase_index),
            "confidence": result.confidence,
            "input_window_start": _iso_z(vector.timestamp),
            "input_window_end": _iso_z(_utcnow()),
            "explanation": result.explanation,
        }

        try:
            resp = await self._signal_client.post_ml_prediction(payload)
        except Exception as exc:
            logger.error("Failed to write ml-prediction: %s", exc)
            return False

        if resp.status_code in (200, 201):
            return True
        logger.warning("ml-prediction write returned %s", resp.status_code)
        return False
