"""Phase-aware rolling baseline for Early Anomaly Detection (Section 7.2).

Maintains a bounded rolling history of observed values per
``(phase, group, window, feature)`` key, from which a robust baseline
(median + MAD) is derived. Baselines are phase-specific because what is
"normal" for a group during startup is not normal during stable
production (Section 7.2) — Process State (7.1) is therefore a hard
dependency of this module. Lives entirely in memory, same as the rolling
window buffer (Section 6.3) — it grows from live operation, never from a
pre-existing dataset (none exists, Section 3.2).
"""

from __future__ import annotations

from collections import deque

import numpy as np

_MAD_TO_STD = 1.4826  # scales MAD to be comparable to a normal std-dev.
_MIN_MAD = 1e-6  # floor to avoid divide-by-zero on a perfectly flat baseline.

_Key = tuple[str, str, str, str]  # (phase, group, window, feature)


class BaselineTracker:
    """Per-(phase, group, window, feature) rolling robust baseline."""

    def __init__(self, history_size: int = 500) -> None:
        self._history_size = history_size
        self._history: dict[_Key, deque] = {}

    def update(
        self, phase: str, group: str, window: str, feature: str, value: float | None
    ) -> None:
        """Append one observation to the rolling history for this key."""
        if value is None:
            return
        key = (phase, group, window, feature)
        history = self._history.setdefault(key, deque(maxlen=self._history_size))
        history.append(float(value))

    def sample_count(self, phase: str, group: str, window: str, feature: str) -> int:
        """Number of observations currently held for this key."""
        key = (phase, group, window, feature)
        return len(self._history.get(key, ()))

    def score(
        self, phase: str, group: str, window: str, feature: str, value: float
    ) -> float | None:
        """Return the robust z-score of ``value`` against the rolling baseline.

        Uses the history collected *before* this observation — the current
        value is never part of its own baseline. Returns ``None`` if no
        history exists yet for this key.
        """
        key = (phase, group, window, feature)
        history = self._history.get(key)
        if not history:
            return None
        arr = np.array(history, dtype=np.float64)
        median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median))) * _MAD_TO_STD
        mad = max(mad, _MIN_MAD)
        return (float(value) - median) / mad

    def baseline_summary(
        self, phase: str, group: str, window: str, feature: str
    ) -> dict | None:
        """Return {median, mad, n} for a key, or None if no history yet."""
        key = (phase, group, window, feature)
        history = self._history.get(key)
        if not history:
            return None
        arr = np.array(history, dtype=np.float64)
        median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median))) * _MAD_TO_STD
        return {"median": round(median, 4), "mad": round(mad, 4), "n": len(history)}
