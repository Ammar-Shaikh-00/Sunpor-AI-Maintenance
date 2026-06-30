import copy
import threading
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CachedSignalValue:
    value_raw: float
    value_scaled: float
    quality: str
    updated_at: datetime


class SignalValueCache:
    """Thread-safe runtime store for latest known MQTT signal values."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._values: dict[str, CachedSignalValue] = {}

    def update(
        self,
        wincc_tag: str,
        value_raw: float,
        value_scaled: float,
        quality: str,
        updated_at: datetime,
    ) -> None:
        with self._lock:
            self._values[wincc_tag] = CachedSignalValue(
                value_raw=value_raw,
                value_scaled=value_scaled,
                quality=quality,
                updated_at=updated_at,
            )

    def snapshot(self) -> dict[str, CachedSignalValue]:
        with self._lock:
            return copy.deepcopy(self._values)

    def count(self) -> int:
        with self._lock:
            return len(self._values)

    def initialize(self, values: dict[str, CachedSignalValue]) -> int:
        with self._lock:
            self._values = copy.deepcopy(values)
            return len(self._values)
