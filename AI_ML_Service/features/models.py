"""Typed output of the feature engine.

``FeatureVector`` is the only input the ML / state / anomaly layers consume.
Feature keys always use ``signal_id`` (never signal name or wincc_tag) and are
qualified with the window they belong to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalFeatures:
    """Derived features for a single signal over one window."""

    signal_id: int
    signal_group: str
    mean: float | None
    std: float | None
    trend: float | None  # linear regression slope per sample
    roc: float | None  # (last - first) / n
    min_val: float | None
    max_val: float | None
    last_val: float | None
    sample_count: int
    has_bad_quality: bool  # True if any entry in window != GOOD


@dataclass
class WindowFeatures:
    """Per-window slice of the feature engine output for one model."""

    window_key: str  # "1min", "5min", "15min", "30min", "full_run"
    sample_count: int  # samples requested for this window (window size)
    signal_features: dict[int, SignalFeatures]  # signal_id -> features
    is_ready: bool  # ratio of signals with >= MIN_SAMPLES meets threshold
    ready_ratio: float


@dataclass
class FeatureVector:
    """Features for all signals feeding one ML model, across every window."""

    model_key: str
    timestamp: datetime  # UTC, time of computation
    windows: dict[str, WindowFeatures]  # window_key -> WindowFeatures
    is_ready: bool  # True when the primary window (e.g. "5min") is ready
    # {"{signal_id}__{window_key}__{feature}": value}; None features excluded.
    features_flat: dict[str, float] = field(default_factory=dict)
