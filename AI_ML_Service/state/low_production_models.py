"""Typed outputs for the Low-Production Cause & Severity sub-analysis.

Extension of Process State (Section 7.1) — not a separate capability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CauseCandidate:
    cause_name: str
    confidence: float
    is_planned: bool
    evidence: str


@dataclass
class LowProductionResult:
    severity: float
    duration_ticks: int
    duration_sec: float
    cause_name: str
    confidence: float
    is_planned: bool
    evidence: str
