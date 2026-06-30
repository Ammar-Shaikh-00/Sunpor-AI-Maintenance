"""In-memory rolling window buffer.

Holds the last N readings per signal using fixed-length deques. This buffer
is the input to feature computation. It lives entirely in memory — no DB, no
file persistence.
"""

from __future__ import annotations

from collections import deque
from typing import Optional


class RollingWindowBuffer:
    """Fixed-size rolling history of readings, keyed by signal id."""

    def __init__(self, signal_ids: list[int], window_size: int) -> None:
        self._window_size = window_size
        self._buffers: dict[int, deque] = {
            signal_id: deque(maxlen=window_size) for signal_id in signal_ids
        }

    def push(
        self, signal_id: int, timestamp: str, value_scaled: float, quality: str
    ) -> None:
        """Append a reading; auto-registers unknown signals."""
        buffer = self._buffers.get(signal_id)
        if buffer is None:
            buffer = deque(maxlen=self._window_size)
            self._buffers[signal_id] = buffer
        buffer.append(
            {
                "timestamp": timestamp,
                "value_scaled": value_scaled,
                "quality": quality,
            }
        )

    def get_window(self, signal_id: int) -> list[dict]:
        """Return all entries (oldest first) for a signal."""
        buffer = self._buffers.get(signal_id)
        return list(buffer) if buffer else []

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
