"""In-memory rolling window buffer.

Holds the last N readings per signal using fixed-length deques. This buffer
is the input to feature computation. It lives entirely in memory — no DB, no
file persistence.

One large deque per signal (``maxlen = max_samples``, sourced from
``config.MAX_BUFFER_SAMPLES``). The feature engine slices the tail using
:meth:`get_last_n` to compute per-window features.
"""

from __future__ import annotations

from collections import deque
from itertools import islice
from typing import Optional

from core.config import get_settings


class RollingWindowBuffer:
    """Fixed-size rolling history of readings, keyed by signal id."""

    def __init__(
        self, signal_ids: list[int], max_samples: Optional[int] = None
    ) -> None:
        if max_samples is None:
            max_samples = get_settings().MAX_BUFFER_SAMPLES
        self._max_samples = max_samples
        self._buffers: dict[int, deque] = {
            signal_id: deque(maxlen=max_samples) for signal_id in signal_ids
        }

    def push(
        self, signal_id: int, timestamp: str, value_scaled: float, quality: str
    ) -> None:
        """Append a reading; auto-registers unknown signals."""
        buffer = self._buffers.get(signal_id)
        if buffer is None:
            buffer = deque(maxlen=self._max_samples)
            self._buffers[signal_id] = buffer
        buffer.append(
            {
                "timestamp": timestamp,
                "value_scaled": value_scaled,
                "quality": quality,
            }
        )

    def get_window(self, signal_id: int) -> list[dict]:
        """Return all buffered entries (oldest first) for a signal."""
        buffer = self._buffers.get(signal_id)
        return list(buffer) if buffer else []

    def get_last_n(self, signal_id: int, n: int) -> list[dict]:
        """Return the most recent ``n`` entries (oldest-first within the slice).

        - Never raises: unknown signal → ``[]``.
        - Empty buffer → ``[]``.
        - ``n`` larger than what we have → returns everything available.
        - ``n <= 0`` → ``[]``.
        """
        try:
            if n <= 0:
                return []
            buffer = self._buffers.get(signal_id)
            if not buffer:
                return []
            size = len(buffer)
            if n >= size:
                return list(buffer)
            # Tail slice — cheaper than list(buffer)[-n:] for large deques.
            return list(islice(buffer, size - n, size))
        except Exception:
            return []

    def get_latest(self, signal_id: int) -> Optional[dict]:
        """Return the most recent entry, or None if empty/unknown."""
        buffer = self._buffers.get(signal_id)
        if not buffer:
            return None
        return buffer[-1]

    def get_window_values(self, signal_id: int) -> list[float]:
        """Return just the scaled values (oldest first) for feature compute."""
        buffer = self._buffers.get(signal_id)
        if not buffer:
            return []
        return [entry["value_scaled"] for entry in buffer]

    def is_ready(self, signal_id: int, min_samples: int) -> bool:
        """True if the signal has at least ``min_samples`` entries."""
        buffer = self._buffers.get(signal_id)
        return bool(buffer) and len(buffer) >= min_samples

    def snapshot(self) -> dict[int, int]:
        """Return {signal_id: current_buffer_length} for status reporting."""
        return {signal_id: len(buffer) for signal_id, buffer in self._buffers.items()}
