"""Process state detector.

Ties the pipeline together: aggregate a FeatureVector into group features,
evaluate the YAML rules, record history, and write a prediction to the backend.
``on_tick`` is gated by readiness + a poll cadence and never raises.
"""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone

from core.config import get_settings
from features.feature_catalog import FeatureCatalog
from state.group_aggregator import GroupAggregator
from state.prediction_writer import PredictionWriter
from state.rule_engine import RuleEngine

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProcessStateDetector:
    """Rule-based process state detection over the process_state FeatureVector."""

    def __init__(
        self,
        catalog: list[dict],
        feature_catalog: FeatureCatalog,
        rules_config_path: str,
        signal_client,
        auth_client,
    ) -> None:
        self._aggregator = GroupAggregator(catalog)
        self._rule_engine = RuleEngine(rules_config_path)
        self._writer = PredictionWriter(signal_client, auth_client)
        settings = get_settings()
        self._predict_every = settings.PREDICT_EVERY_N_POLLS
        # Rule-based state uses the primary window (5min by default).
        self._window_key = settings.PRIMARY_WINDOW_KEY

        self.last_result = None
        self.history = deque(maxlen=100)

    @property
    def rule_engine(self) -> RuleEngine:
        return self._rule_engine

    @property
    def writer(self) -> PredictionWriter:
        """Expose the shared PredictionWriter for Process State extensions."""
        return self._writer

    async def on_tick(self, vector, poll_count: int):
        """Evaluate the current vector and write a prediction (cadence-gated).

        Returns the ``StateResult`` on a successful evaluation, otherwise
        ``None`` (not ready / cadence skip / error). The poller passes this
        straight into LowProductionAnalyzer.
        """
        if not vector.is_ready:
            return None
        primary = vector.windows.get(self._window_key)
        if primary is None:
            return None
        if primary.ready_ratio < self._rule_engine.min_vector_ready_ratio:
            return None
        if self._predict_every <= 0 or poll_count % self._predict_every != 0:
            return None

        try:
            group_features = self._aggregator.aggregate(
                vector, window_key=self._window_key
            )
            result = self._rule_engine.evaluate(group_features)
            self.last_result = result
            self.history.append(
                {
                    "timestamp": _utcnow().isoformat(),
                    "phase_name": result.phase_name,
                    "confidence": result.confidence,
                    "is_fallback": result.is_fallback,
                    "is_confirmed_phase": result.is_confirmed_phase,
                }
            )
            await self._writer.write_prediction(
                result, vector, window_key=self._window_key
            )
            logger.info(
                "[STATE] phase=%s conf=%s calibrated=%s fallback=%s",
                result.phase_name,
                result.confidence,
                result.is_confirmed_phase,
                result.is_fallback,
            )
            return result
        except Exception as exc:  # on_tick must never raise
            logger.error("ProcessStateDetector.on_tick failed: %s", exc)
            return None

    def get_status(self) -> dict:
        if self.last_result is None:
            return {"status": "not_ready"}
        r = self.last_result
        return {
            "phase_name": r.phase_name,
            "phase_index": r.phase_index,
            "confidence": r.confidence,
            "is_fallback": r.is_fallback,
            "is_confirmed_phase": r.is_confirmed_phase,
            "explanation": r.explanation,
        }

    def get_history(self) -> list[dict]:
        return list(self.history)
