"""Data cleaning pipeline.

Sits between the raw API response and the rolling window buffer. Every poll
snapshot passes through :meth:`DataCleaner.clean_snapshot`, which validates
types, filters unknown signals, deduplicates,
verifies factor scaling, evaluates quality, and detects missing signals.

The cleaner never raises: any problem produces an invalid record with notes.
Only ``CleanRecord`` instances leave this layer — raw API dicts never reach
the buffer, feature engine, or ML.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from cleaning.models import CleanRecord, CleaningReport
from core.quality_rules import BAD, GOOD, MISSING

logger = logging.getLogger(__name__)

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DataCleaner:
    """Validates and normalizes raw snapshots into CleanRecords."""

    def __init__(self, catalog: list[dict], quality_evaluator) -> None:
        self._catalog_map: dict[int, dict] = {
            s["id"]: {
                "wincc_tag": s.get("wincc_tag", ""),
                "factor": s.get("factor", 1) or 1,
                "signal_group": s.get("signal_group", ""),
            }
            for s in catalog
            if s.get("id") is not None
        }
        self._quality = quality_evaluator
        # signal_id -> last seen dedup key (stateful across polls).
        self._dedup_cache: dict[int, str] = {}

    def clean_snapshot(
        self, raw_snapshot: list[dict]
    ) -> tuple[list[CleanRecord], CleaningReport]:
        """Run the full cleaning pipeline over one snapshot."""
        records: list[CleanRecord] = []
        type_errors = 0
        duplicate_dropped = 0
        quality_counts: dict[str, int] = {}

        def bump(quality: str) -> None:
            quality_counts[quality] = quality_counts.get(quality, 0) + 1

        raw_list = raw_snapshot if isinstance(raw_snapshot, list) else []
        seen_signal_ids = self._collect_seen_ids(raw_list)

        for entry in raw_list:
            if not isinstance(entry, dict):
                type_errors += 1
                records.append(self._invalid(-1, ["type_error"]))
                bump(BAD)
                continue

            # STEP 1 — TYPE VALIDATION
            try:
                signal_id = int(entry["signal_id"])
                value_raw = float(entry["value_raw"])
                raw_scaled = entry.get("value_scaled")
                value_scaled = float(raw_scaled) if raw_scaled is not None else None
            except (KeyError, TypeError, ValueError):
                type_errors += 1
                recovered_id = self._safe_int(entry.get("signal_id"))
                records.append(self._invalid(recovered_id, ["type_error"]))
                bump(BAD)
                continue

            # STEP 2 — UNKNOWN SIGNAL FILTER
            meta = self._catalog_map.get(signal_id)
            if meta is None:
                records.append(self._invalid(signal_id, ["unknown_signal_id"]))
                bump(BAD)
                continue

            # STEP 3 — TIMESTAMP (passed through from backend as UTC)
            raw_ts = entry.get("timestamp")
            if raw_ts is None or raw_ts == "":
                records.append(
                    self._invalid(signal_id, ["missing_timestamp"], meta=meta)
                )
                bump(BAD)
                continue
            if isinstance(raw_ts, datetime):
                ts = raw_ts
            else:
                try:
                    ts = datetime.fromisoformat(str(raw_ts))
                except ValueError:
                    records.append(
                        self._invalid(signal_id, ["invalid_timestamp"], meta=meta)
                    )
                    bump(BAD)
                    continue

            # STEP 4 — DEDUPLICATION
            key = f"{signal_id}|{raw_ts}"
            if self._dedup_cache.get(signal_id) == key:
                duplicate_dropped += 1
                continue
            self._dedup_cache[signal_id] = key

            # STEP 5 — VALUE SCALING VERIFICATION
            notes: list[str] = []
            factor = meta["factor"]
            expected_scaled = round(value_raw * factor, 4)
            if value_scaled is None or abs(value_scaled - expected_scaled) > 0.01:
                value_scaled = expected_scaled
                notes.append("scaled_corrected")

            # STEP 6 — QUALITY EVALUATION
            quality = self._quality.evaluate(signal_id, value_raw)
            if quality != GOOD:
                notes.append(f"quality:{quality}")

            # STEP 7 — BUILD CleanRecord (passed all hard checks)
            records.append(
                CleanRecord(
                    signal_id=signal_id,
                    wincc_tag=meta["wincc_tag"],
                    timestamp=ts,
                    value_raw=value_raw,
                    value_scaled=value_scaled,
                    quality=quality,
                    signal_group=meta["signal_group"],
                    factor=factor,
                    is_valid=True,
                    cleaning_notes=notes,
                )
            )
            bump(quality)

        # STEP 8 — MISSING SIGNAL DETECTION
        missing_signals = [
            sid for sid in self._catalog_map if sid not in seen_signal_ids
        ]
        for sid in missing_signals:
            self._quality.mark_missing(sid)
            meta = self._catalog_map[sid]
            records.append(
                CleanRecord(
                    signal_id=sid,
                    wincc_tag=meta["wincc_tag"],
                    timestamp=_utcnow(),
                    value_raw=0.0,
                    value_scaled=0.0,
                    quality=MISSING,
                    signal_group=meta["signal_group"],
                    factor=meta["factor"],
                    is_valid=False,
                    cleaning_notes=["missing_from_snapshot"],
                )
            )
            bump(MISSING)

        # STEP 9 — BUILD CleaningReport
        total_valid = sum(1 for r in records if r.is_valid)
        total_invalid = sum(1 for r in records if not r.is_valid)
        report = CleaningReport(
            total_received=len(raw_list),
            total_valid=total_valid,
            total_invalid=total_invalid,
            missing_signals=missing_signals,
            quality_counts=quality_counts,
            duplicate_dropped=duplicate_dropped,
            type_errors=type_errors,
            timestamp=_utcnow(),
        )
        return records, report

    def _invalid(
        self,
        signal_id: int,
        notes: list[str],
        meta: dict | None = None,
        timestamp: datetime | None = None,
    ) -> CleanRecord:
        """Build an is_valid=False BAD record with the given notes."""
        meta = meta or {}
        return CleanRecord(
            signal_id=signal_id,
            wincc_tag=meta.get("wincc_tag", ""),
            timestamp=timestamp or _utcnow(),
            value_raw=0.0,
            value_scaled=0.0,
            quality=BAD,
            signal_group=meta.get("signal_group", ""),
            factor=meta.get("factor", 1),
            is_valid=False,
            cleaning_notes=notes,
        )

    def _collect_seen_ids(self, raw_list: list) -> set[int]:
        """Best-effort set of signal_ids present in the raw snapshot."""
        seen: set[int] = set()
        for entry in raw_list:
            if isinstance(entry, dict):
                sid = self._safe_int(entry.get("signal_id"))
                if sid is not None:
                    seen.add(sid)
        return seen

    @staticmethod
    def _safe_int(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

