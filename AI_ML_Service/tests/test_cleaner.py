"""Unit tests for the data cleaning pipeline."""

from datetime import datetime, timezone

from cleaning.cleaner import DataCleaner
from cleaning.models import CleanRecord, CleaningReport


class StubEvaluator:
    """Minimal quality evaluator: configurable verdict, records missing calls."""

    def __init__(self, verdict: str = "GOOD") -> None:
        self.verdict = verdict
        self.missing_calls: list[int] = []

    def evaluate(self, signal_id: int, value_raw: float) -> str:
        return self.verdict

    def mark_missing(self, signal_id: int) -> str:
        self.missing_calls.append(signal_id)
        return "MISSING"


def _catalog() -> list[dict]:
    return [
        {"id": 1, "wincc_tag": "TAG_F", "factor": 1, "signal_group": "feeders"},
        {"id": 2, "wincc_tag": "TAG_P", "factor": 0.1, "signal_group": "melt_pressure"},
        {"id": 3, "wincc_tag": "TAG_S", "factor": 1, "signal_group": "status"},
    ]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entry(signal_id, value_raw, value_scaled, ts=None, quality="good"):
    return {
        "signal_id": signal_id,
        "wincc_tag": f"TAG_{signal_id}",
        "value_raw": value_raw,
        "value_scaled": value_scaled,
        "quality": quality,
        "timestamp": ts or _now_iso(),
        "source": "MQTT",
    }


def _by_id(records, signal_id):
    return next(r for r in records if r.signal_id == signal_id)


def test_valid_record_passes_all_steps():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    records, report = cleaner.clean_snapshot(
        [_entry(1, 100.0, 100.0), _entry(2, 50.0, 5.0), _entry(3, 1.0, 1.0)]
    )
    rec = _by_id(records, 1)
    assert rec.is_valid is True
    assert rec.quality == "GOOD"
    assert isinstance(rec, CleanRecord)
    assert isinstance(report, CleaningReport)


def test_type_error_invalidates_record():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    records, report = cleaner.clean_snapshot(
        [_entry(1, "not_a_float", 1.0), _entry(2, 50.0, 5.0), _entry(3, 1.0, 1.0)]
    )
    rec = _by_id(records, 1)
    assert rec.is_valid is False
    assert rec.quality == "BAD"
    assert "type_error" in rec.cleaning_notes
    assert report.type_errors == 1


def test_duplicate_dropped():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    ts = _now_iso()
    # First poll registers signal 1; second identical poll is a duplicate.
    cleaner.clean_snapshot([_entry(1, 100.0, 100.0, ts=ts)])
    records, report = cleaner.clean_snapshot([_entry(1, 100.0, 100.0, ts=ts)])
    assert report.duplicate_dropped == 1
    # Signal 1 not present as a valid record this round.
    assert all(not (r.signal_id == 1 and r.is_valid) for r in records)


def test_missing_signal_detected():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    # Snapshot has only signals 1 and 2 → signal 3 missing.
    records, report = cleaner.clean_snapshot(
        [_entry(1, 100.0, 100.0), _entry(2, 50.0, 5.0)]
    )
    assert report.missing_signals == [3]
    missing = [r for r in records if r.quality == "MISSING"]
    assert len(missing) == 1
    assert missing[0].signal_id == 3
    assert missing[0].is_valid is False


def test_scaled_value_corrected():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    # signal 2 factor 0.1: 2300 × 0.1 = 230.0, but reported scaled is wrong.
    records, _ = cleaner.clean_snapshot([_entry(2, 2300.0, 999.0)])
    rec = _by_id(records, 2)
    assert rec.value_scaled == 230.0
    assert "scaled_corrected" in rec.cleaning_notes


def test_cleaning_report_counts_correct():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    # 1 valid (signal 1), 1 type error (signal 2). Signal 3 missing.
    records, report = cleaner.clean_snapshot(
        [_entry(1, 100.0, 100.0), _entry(2, "bad", 5.0)]
    )
    assert report.total_received == 2
    assert report.type_errors == 1
    # Valid records exclude invalid + missing.
    assert report.total_valid == sum(1 for r in records if r.is_valid)
    assert report.total_invalid == sum(1 for r in records if not r.is_valid)
    # quality_counts total equals all produced records.
    assert sum(report.quality_counts.values()) == len(records)


def test_unknown_signal_filtered():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    records, _ = cleaner.clean_snapshot([_entry(99, 1.0, 1.0)])
    rec = _by_id(records, 99)
    assert rec.is_valid is False
    assert "unknown_signal_id" in rec.cleaning_notes


def test_cleaner_never_raises_on_garbage():
    cleaner = DataCleaner(_catalog(), StubEvaluator("GOOD"))
    records, report = cleaner.clean_snapshot(["garbage", None, 123, {}])
    # Should not raise; all junk handled.
    assert report.total_received == 4
    assert isinstance(records, list)
