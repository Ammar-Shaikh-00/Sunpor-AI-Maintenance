"""Unit tests for the in-memory rolling window buffer."""

from ingestion.window_buffer import RollingWindowBuffer


def test_maxlen_respected_and_latest():
    buf = RollingWindowBuffer([1], window_size=30)
    for i in range(1, 36):  # push 35 entries
        buf.push(1, timestamp=f"t{i}", value_scaled=float(i), quality="GOOD")

    window = buf.get_window(1)
    assert len(window) == 30  # deque maxlen enforced

    latest = buf.get_latest(1)
    assert latest["value_scaled"] == 35.0
    assert latest["timestamp"] == "t35"

    # Oldest retained entry is #6 (1..5 dropped).
    assert window[0]["value_scaled"] == 6.0


def test_is_ready_thresholds():
    buf = RollingWindowBuffer([1], window_size=30)
    for i in range(35):
        buf.push(1, timestamp=f"t{i}", value_scaled=float(i), quality="GOOD")

    assert buf.is_ready(1, min_samples=30) is True
    assert buf.is_ready(1, min_samples=31) is False


def test_window_values_and_empty():
    buf = RollingWindowBuffer([1, 2], window_size=5)
    buf.push(1, "t0", 1.5, "GOOD")
    buf.push(1, "t1", 2.5, "STALE")

    assert buf.get_window_values(1) == [1.5, 2.5]
    # Signal 2 has no readings yet.
    assert buf.get_window_values(2) == []
    assert buf.get_latest(2) is None
    assert buf.is_ready(2, min_samples=1) is False


def test_snapshot_lengths():
    buf = RollingWindowBuffer([1, 2], window_size=10)
    buf.push(1, "t0", 1.0, "GOOD")
    buf.push(1, "t1", 1.0, "GOOD")
    buf.push(2, "t0", 5.0, "GOOD")

    assert buf.snapshot() == {1: 2, 2: 1}


def test_unknown_signal_autoregisters():
    buf = RollingWindowBuffer([1], window_size=3)
    buf.push(99, "t0", 7.0, "GOOD")
    assert buf.get_latest(99)["value_scaled"] == 7.0
    assert buf.snapshot()[99] == 1
