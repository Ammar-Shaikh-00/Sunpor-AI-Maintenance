"""Typed data contracts for the cleaning layer.

All downstream code (buffer, feature engine, ML) consumes ``CleanRecord``
only — never raw API dicts. ``CleaningReport`` summarizes one poll cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CleanRecord:
    """A single validated, normalized signal reading."""

    signal_id: int
    wincc_tag: str
    timestamp: datetime  # UTC from backend
    value_raw: float
    value_scaled: float  # verified: value_raw × factor
    quality: str  # GOOD | STALE | OUT_OF_RANGE | MISSING | BAD
    signal_group: str
    factor: float
    is_valid: bool  # False → excluded from feature engine
    cleaning_notes: list[str] = field(default_factory=list)


@dataclass
class CleaningReport:
    """Summary of one cleaning pass over a snapshot."""

    total_received: int
    total_valid: int
    total_invalid: int
    missing_signals: list[int]  # signal_ids not in snapshot
    quality_counts: dict  # {"GOOD": n, "STALE": n, ...}
    duplicate_dropped: int
    type_errors: int
    timestamp: datetime
