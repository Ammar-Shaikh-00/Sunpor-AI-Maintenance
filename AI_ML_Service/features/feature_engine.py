"""Feature engine.

Reads CleanRecord windows from the RollingWindowBuffer, computes derived
features per signal, and groups them per ML model using the FeatureCatalog.
Output is a ``FeatureVector`` per model_key — the only input the ML layer
consumes.

Stateless per call (all history lives in the buffer); the engine only caches
the most recent vector per model for status/inspection endpoints. It never
calls the backend API and ``on_tick`` never raises.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np

from core.config import get_settings
from core.quality_rules import GOOD
from features.feature_catalog import FeatureCatalog
from features.models import FeatureVector, SignalFeatures

logger = logging.getLogger(__name__)

# Feature names emitted into features_flat (order is stable).
FLAT_FEATURES = ("mean", "std", "trend", "roc", "min_val", "max_val", "last_val")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FeatureEngine:
    """Computes per-model FeatureVectors from buffer windows."""

    def __init__(
        self,
        catalog: list[dict],
        feature_catalog: FeatureCatalog,
        min_samples: int | None = None,
        ready_ratio_threshold: float | None = None,
    ) -> None:
        settings = get_settings()
        self._catalog_map = {
            s["id"]: s for s in catalog if s.get("id") is not None
        }
        self._feature_catalog = feature_catalog
        self._min_samples = (
            min_samples if min_samples is not None else settings.MIN_SAMPLES
        )
        self._ready_ratio_threshold = (
            ready_ratio_threshold
            if ready_ratio_threshold is not None
            else settings.READY_RATIO_THRESHOLD
        )
        self.last_vectors: dict[str, FeatureVector] = {}

    def on_tick(self, window_buffer) -> dict[str, FeatureVector]:
        """Recompute all model vectors from the current buffer state."""
        try:
            for model_key in self._feature_catalog.summary():
                signal_ids = self._feature_catalog.get_signals_for_model(model_key)
                vector = self._compute_vector(model_key, signal_ids, window_buffer)
                self.last_vectors[model_key] = vector
            return dict(self.last_vectors)
        except Exception as exc:  # on_tick must never raise
            logger.error("Feature engine on_tick failed: %s", exc)
            return {}

    def _compute_vector(
        self, model_key: str, signal_ids: list[int], window_buffer
    ) -> FeatureVector:
        signal_features: dict[int, SignalFeatures] = {}
        ready_count = 0

        for signal_id in signal_ids:
            window = window_buffer.get_window(signal_id)
            sf = self._compute_signal_features(signal_id, window)
            signal_features[signal_id] = sf
            if sf.sample_count >= self._min_samples:
                ready_count += 1

        total = len(signal_ids)
        ready_ratio = ready_count / total if total else 0.0
        is_ready = ready_ratio >= self._ready_ratio_threshold

        return FeatureVector(
            model_key=model_key,
            timestamp=_utcnow(),
            signal_features=signal_features,
            is_ready=is_ready,
            ready_ratio=round(ready_ratio, 3),
            features_flat=self._flatten(signal_features),
        )

    def _compute_signal_features(
        self, signal_id: int, window: list[dict]
    ) -> SignalFeatures:
        group = self._catalog_map.get(signal_id, {}).get("signal_group", "")

        if not window:
            return SignalFeatures(
                signal_id=signal_id,
                signal_group=group,
                mean=None,
                std=None,
                trend=None,
                roc=None,
                min_val=None,
                max_val=None,
                last_val=None,
                sample_count=0,
                has_bad_quality=False,
            )

        values = [e["value_scaled"] for e in window]
        qualities = [e["quality"] for e in window]
        arr = np.array(values, dtype=np.float64)
        n = int(arr.size)

        mean = float(np.mean(arr))
        std = float(np.std(arr)) if n > 1 else 0.0
        min_v = float(np.min(arr))
        max_v = float(np.max(arr))
        last_v = float(arr[-1])
        roc = float(arr[-1] - arr[0]) / n if n > 1 else 0.0

        if n > 1:
            x = np.arange(n, dtype=np.float64)
            slope = float(np.polyfit(x, arr, 1)[0])
        else:
            slope = 0.0

        has_bad = any(q != GOOD for q in qualities)

        return SignalFeatures(
            signal_id=signal_id,
            signal_group=group,
            mean=round(mean, 4),
            std=round(std, 4),
            trend=round(slope, 6),
            roc=round(roc, 4),
            min_val=round(min_v, 4),
            max_val=round(max_v, 4),
            last_val=round(last_v, 4),
            sample_count=n,
            has_bad_quality=has_bad,
        )

    @staticmethod
    def _flatten(signal_features: dict[int, SignalFeatures]) -> dict[str, float]:
        """Flatten to {"{signal_id}__{feature}": value}, skipping None."""
        flat: dict[str, float] = {}
        for signal_id, sf in signal_features.items():
            for feature in FLAT_FEATURES:
                value = getattr(sf, feature)
                if value is not None:
                    flat[f"{signal_id}__{feature}"] = value
        return flat

    def get_vector(self, model_key: str) -> FeatureVector | None:
        """Return the most recent FeatureVector for a model, if any."""
        return self.last_vectors.get(model_key)

    def summary(self) -> dict:
        """Per-model readiness summary for status endpoints."""
        result = {}
        for model_key, vector in self.last_vectors.items():
            result[model_key] = {
                "is_ready": vector.is_ready,
                "ready_ratio": vector.ready_ratio,
                "signal_count": len(vector.signal_features),
                "computed_at": vector.timestamp.isoformat(),
            }
        return result
