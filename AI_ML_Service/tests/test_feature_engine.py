"""Unit tests for the feature engine."""

from features.feature_engine import FeatureEngine
from features.models import FeatureVector
from ingestion.window_buffer import RollingWindowBuffer


class FakeFeatureCatalog:
    """Minimal stand-in: 2 models, 2 signals each."""

    def __init__(self, mapping: dict[str, list[int]]) -> None:
        self._mapping = mapping

    def summary(self) -> dict:
        return {k: len(v) for k, v in self._mapping.items()}

    def get_signals_for_model(self, model_key: str) -> list[int]:
        return list(self._mapping.get(model_key, []))


def _catalog() -> list[dict]:
    # 4 signals across 2 groups.
    return [
        {"id": 1, "signal_group": "feeders"},
        {"id": 2, "signal_group": "feeders"},
        {"id": 3, "signal_group": "melt_pressure"},
        {"id": 4, "signal_group": "melt_pressure"},
    ]


def _feature_catalog() -> FakeFeatureCatalog:
    return FakeFeatureCatalog({"model_a": [1, 2], "model_b": [3, 4]})


def _push(buffer, signal_id, values, quality="GOOD"):
    for i, v in enumerate(values):
        q = quality[i] if isinstance(quality, list) else quality
        buffer.push(signal_id, f"t{i}", float(v), q)


def test_compute_signal_features_correct():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1, 2, 3, 4], window_size=30)
    _push(buffer, 1, [1.0, 2.0, 3.0])

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.mean == 2.0
    assert sf.roc == round(2.0 / 3.0, 4)  # (last - first) / n = (3 - 1) / 3
    assert sf.trend > 0
    assert sf.std > 0
    assert sf.last_val == 3.0
    assert sf.min_val == 1.0
    assert sf.max_val == 3.0
    assert sf.sample_count == 3


def test_empty_window_returns_none_features():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1, 2, 3, 4], window_size=30)

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.sample_count == 0
    assert sf.mean is None
    assert sf.std is None
    assert sf.trend is None
    assert sf.has_bad_quality is False


def test_is_ready_requires_80_percent():
    # 4 signals in one model; only 3 have >= min_samples -> 0.75 -> not ready.
    fc = FakeFeatureCatalog({"model_a": [1, 2, 3, 4]})
    engine = FeatureEngine(_catalog(), fc, min_samples=10)
    buffer = RollingWindowBuffer([1, 2, 3, 4], window_size=30)
    for sid in (1, 2, 3):
        _push(buffer, sid, list(range(12)))  # 12 >= 10
    _push(buffer, 4, [1.0, 2.0])  # only 2 < 10

    vector = engine._compute_vector("model_a", [1, 2, 3, 4], buffer)
    assert vector.ready_ratio == 0.75
    assert vector.is_ready is False


def test_flatten_excludes_none():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1, 2], window_size=30)
    _push(buffer, 1, [1.0, 2.0, 3.0])
    # signal 2 has no data -> all None.

    vector = engine._compute_vector("model_a", [1, 2], buffer)
    # Signal 1 keys present.
    assert "1__mean" in vector.features_flat
    # Signal 2 (empty) excluded entirely.
    assert not any(k.startswith("2__") for k in vector.features_flat)


def test_has_bad_quality_flagged():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1], window_size=30)
    qualities = ["GOOD"] * 8 + ["STALE", "STALE"]
    _push(buffer, 1, list(range(10)), quality=qualities)

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.has_bad_quality is True


def test_on_tick_returns_all_models():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1, 2, 3, 4], window_size=30)
    for sid in (1, 2, 3, 4):
        _push(buffer, sid, list(range(12)))

    result = engine.on_tick(buffer)
    assert set(result.keys()) == {"model_a", "model_b"}
    assert all(isinstance(v, FeatureVector) for v in result.values())


def test_on_tick_never_raises():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)

    class BrokenBuffer:
        def get_window(self, signal_id):
            raise RuntimeError("boom")

    # Should swallow the error and return {}.
    assert engine.on_tick(BrokenBuffer()) == {}


def test_roc_value_precise():
    engine = FeatureEngine(_catalog(), _feature_catalog(), min_samples=2)
    buffer = RollingWindowBuffer([1], window_size=30)
    _push(buffer, 1, [1.0, 2.0, 3.0])
    sf = engine._compute_signal_features(1, buffer.get_window(1))
    # roc = (last - first) / n = (3 - 1) / 3 = 0.6667
    assert sf.roc == round(2.0 / 3.0, 4)
