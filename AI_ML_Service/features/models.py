"""Typed output of the feature engine.

``FeatureVector`` is the only input the ML / state / anomaly layers consume.
Feature keys always use ``signal_id`` (never signal name or wincc_tag).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalFeatures:
    """Derived features for a single signal over its rolling window."""

    signal_id: int
    signal_group: str
    mean: float | None  # mean of value_scaled over window
    std: float | None  # standard deviation
    trend: float | None  # linear regression slope (per sample)
    roc: float | None  # rate of change: (last - first) / n
    min_val: float | None
    max_val: float | None
    last_val: float | None
    sample_count: int
    has_bad_quality: bool  # True if any entry in window != GOOD


@dataclass
class FeatureVector:
    """Features for all signals feeding one ML model."""

    model_key: str
    timestamp: datetime  # UTC, time of computation
    signal_features: dict[int, SignalFeatures]  # signal_id -> SignalFeatures
    is_ready: bool  # True if min_samples met for enough signals
    ready_ratio: float  # signals_ready / total_signals
    # {"{signal_id}__{feature}": value}; None features excluded.
    features_flat: dict[str, float] = field(default_factory=dict)
