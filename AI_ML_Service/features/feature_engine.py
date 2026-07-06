"""Feature engine.

Reads CleanRecord windows from the ``RollingWindowBuffer``, slices multiple
time windows out of each signal's tail, and computes derived features per
window per signal. Windows come from ``config.FEATURE_WINDOWS`` — never
hardcoded. Output is a :class:`FeatureVector` per model_key, which is the
only input the ML / anomaly / state layers consume.

Stateless per call (all history lives in the buffer); the engine only caches
the most recent vector per model for status endpoints. It never calls the
backend API and ``on_tick`` never raises.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import numpy as np

from core.config import get_settings
from core.quality_rules import BAD, GOOD, OUT_OF_RANGE
from features.feature_catalog import FeatureCatalog
from features.models import FeatureVector, SignalFeatures, WindowFeatures

logger = logging.getLogger(__name__)

# Only physically impossible values or source-flagged bad values are treated as
# hard faults. STALE / MISSING are data-availability issues, not machine faults.
_HARD_FAULT_QUALITIES = frozenset({OUT_OF_RANGE, BAD})

# (flat suffix, SignalFeatures attribute). Order is stable across polls.
_FLAT_FEATURES: tuple[tuple[str, str], ...] = (
    ("mean", "mean"),
    ("std", "std"),
    ("trend", "trend"),
    ("roc", "roc"),
    ("min_val", "min_val"),
    ("max_val", "max_val"),
    ("last_val", "last_val"),
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(ts: str) -> datetime | None:
    """Parse an ISO timestamp string as UTC (handles trailing Z)."""
    if not ts:
        return None
    try:
        normalized = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError):
        return None


def _window_bounds_from_entries(
    entries: list[dict],
) -> tuple[datetime | None, datetime | None]:
    """Return (oldest, newest) timestamp from buffer entries, or (None, None)."""
    timestamps: list[datetime] = []
    for entry in entries:
        ts = _parse_timestamp(entry.get("timestamp", ""))
        if ts is not None:
            timestamps.append(ts)
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


class FeatureEngine:
    """Computes per-model, multi-window ``FeatureVector`` s from buffer windows."""

    def __init__(
        self,
        catalog: list[dict],
        feature_catalog: FeatureCatalog,
        min_samples: int | None = None,
        ready_ratio_threshold: float | None = None,
        feature_windows: dict[str, int] | None = None,
        primary_window_key: str | None = None,
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
        self._windows: dict[str, int] = dict(
            feature_windows if feature_windows is not None else settings.FEATURE_WINDOWS
        )
        self._primary_window_key = (
            primary_window_key
            if primary_window_key is not None
            else settings.PRIMARY_WINDOW_KEY
        )
        self.last_vectors: dict[str, FeatureVector] = {}

    # ── Public API ─────────────────────────────────────────────────────

    def on_tick(self, window_buffer) -> dict[str, FeatureVector]:
        """Recompute all model vectors for every configured window."""
        try:
            for model_key in self._feature_catalog.summary():
                signal_ids = self._feature_catalog.get_signals_for_model(model_key)
                vector = self._compute_vector(model_key, signal_ids, window_buffer)
                self.last_vectors[model_key] = vector
            return dict(self.last_vectors)
        except Exception as exc:  # on_tick must never raise
            logger.error("Feature engine on_tick failed: %s", exc)
            return {}

    def get_vector(self, model_key: str) -> FeatureVector | None:
        """Return the most recent FeatureVector for a model, if any."""
        return self.last_vectors.get(model_key)

    def summary(self) -> dict:
        """Per-model, per-window readiness summary for status endpoints."""
        result: dict[str, dict] = {}
        for model_key, vector in self.last_vectors.items():
            per_window = {}
            for window_key, wf in vector.windows.items():
                per_window[window_key] = {
                    "is_ready": wf.is_ready,
                    "ready_ratio": wf.ready_ratio,
                }
            result[model_key] = {
                "is_ready": vector.is_ready,
                "primary_window": self._primary_window_key,
                "signal_count": (
                    len(next(iter(vector.windows.values())).signal_features)
                    if vector.windows
                    else 0
                ),
                "computed_at": vector.timestamp.isoformat(),
                "windows": per_window,
            }
        return result

    # ── Internal helpers ───────────────────────────────────────────────

    def _compute_vector(
        self, model_key: str, signal_ids: list[int], window_buffer
    ) -> FeatureVector:
        window_results: dict[str, WindowFeatures] = {}

        for window_key, n_samples in self._windows.items():
            signal_features: dict[int, SignalFeatures] = {}
            ready_count = 0
            entries_for_bounds: list[dict] = []
            # A window is "ready" for a signal when the tail slice reaches the
            # window's own size, floored by MIN_SAMPLES so a signal with too few
            # samples is never counted ready even if a window is smaller.
            required = max(n_samples, self._min_samples)
            for signal_id in signal_ids:
                try:
                    entries = window_buffer.get_last_n(signal_id, n_samples)
                except Exception:
                    entries = []
                entries_for_bounds.extend(entries)
                sf = self._compute_signal_features(signal_id, entries)
                signal_features[signal_id] = sf
                if sf.sample_count >= required:
                    ready_count += 1

            window_start, window_end = _window_bounds_from_entries(entries_for_bounds)
            total = len(signal_ids)
            ratio = ready_count / total if total else 0.0
            window_results[window_key] = WindowFeatures(
                window_key=window_key,
                sample_count=n_samples,
                signal_features=signal_features,
                is_ready=ratio >= self._ready_ratio_threshold,
                ready_ratio=round(ratio, 3),
                window_start=window_start,
                window_end=window_end,
            )

        primary = window_results.get(self._primary_window_key)
        is_ready = bool(primary and primary.is_ready)

        return FeatureVector(
            model_key=model_key,
            timestamp=_utcnow(),
            windows=window_results,
            is_ready=is_ready,
            features_flat=self._flatten_multi_window(window_results),
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
                has_hard_fault=False,
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
        has_hard = any(q in _HARD_FAULT_QUALITIES for q in qualities)

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
            has_hard_fault=has_hard,
        )

    @staticmethod
    def _flatten_multi_window(
        window_results: dict[str, WindowFeatures],
    ) -> dict[str, float]:
        """Flatten to ``{signal_id}__{window_key}__{feature}``; skip None."""
        flat: dict[str, float] = {}
        for window_key, wf in window_results.items():
            for signal_id, sf in wf.signal_features.items():
                prefix = f"{signal_id}__{window_key}"
                for suffix, attr in _FLAT_FEATURES:
                    value = getattr(sf, attr)
                    if value is not None:
                        flat[f"{prefix}__{suffix}"] = value
        return flat
