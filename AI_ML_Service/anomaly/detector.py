"""Anomaly detection (stub).

Per-state anomaly scoring (e.g. Isolation Forest / robust Z-score).
Implementation to follow in a later task.
"""

from __future__ import annotations


class AnomalyDetector:
    """Placeholder for the per-state anomaly detector."""

    def __init__(self) -> None:
        pass

    def score(self, *args, **kwargs):
        """Return an anomaly score for the provided feature window."""
        raise NotImplementedError("AnomalyDetector.score is not implemented yet")
