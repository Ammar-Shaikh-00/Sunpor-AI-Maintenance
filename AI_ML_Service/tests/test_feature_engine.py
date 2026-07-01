"""Unit tests for the multi-window feature engine."""

from features.feature_engine import FeatureEngine
from features.models import FeatureVector, WindowFeatures
from ingestion.window_buffer import RollingWindowBuffer


class FakeFeatureCatalog:
    """Minimal stand-in: N models, N signals each."""

    def __init__(self, mapping: dict[str, list[int]]) -> None:
        self._mapping = mapping

    def summary(self) -> dict:
        return {k: len(v) for k, v in self._mapping.items()}

    def get_signals_for_model(self, model_key: str) -> list[int]:
        return list(self._mapping.get(model_key, []))


# Small window set used in tests — spans "short" and "long".
_TEST_WINDOWS = {"1min": 6, "5min": 30, "15min": 90, "30min": 180, "full_run": 200}


def _catalog() -> list[dict]:
    return [
        {"id": 1, "signal_group": "feeders"},
        {"id": 2, "signal_group": "feeders"},
        {"id": 3, "signal_group": "melt_pressure"},
        {"id": 4, "signal_group": "melt_pressure"},
    ]


def _feature_catalog() -> FakeFeatureCatalog:
    return FakeFeatureCatalog({"model_a": [1, 2], "model_b": [3, 4]})


def _engine(min_samples=2, primary="5min", windows=None):
    return FeatureEngine(
        _catalog(),
        _feature_catalog(),
        min_samples=min_samples,
        feature_windows=windows or _TEST_WINDOWS,
        primary_window_key=primary,
    )


def _push(buffer, signal_id, values, quality="GOOD"):
    for i, v in enumerate(values):
        q = quality[i] if isinstance(quality, list) else quality
        buffer.push(signal_id, f"t{i}", float(v), q)


def test_compute_signal_features_correct():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2, 3, 4], max_samples=300)
    _push(buffer, 1, [1.0, 2.0, 3.0])

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.mean == 2.0
    assert sf.roc == round(2.0 / 3.0, 4)
    assert sf.trend > 0
    assert sf.std > 0
    assert sf.last_val == 3.0
    assert sf.min_val == 1.0
    assert sf.max_val == 3.0
    assert sf.sample_count == 3


def test_empty_window_returns_none_features():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2, 3, 4], max_samples=300)

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.sample_count == 0
    assert sf.mean is None
    assert sf.std is None
    assert sf.trend is None
    assert sf.has_bad_quality is False


def test_multi_window_sizes_computed():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2, 3, 4], max_samples=300)
    for sid in (1, 2, 3, 4):
        _push(buffer, sid, list(range(200)))

    vector = engine._compute_vector("model_a", [1, 2], buffer)
    assert set(vector.windows.keys()) == set(_TEST_WINDOWS.keys())

    # 1min window keeps last 6 samples; 30min keeps last 180.
    assert vector.windows["1min"].signal_features[1].sample_count == 6
    assert vector.windows["30min"].signal_features[1].sample_count == 180
    # full_run window slice is capped at what buffer actually holds (200).
    assert vector.windows["full_run"].signal_features[1].sample_count == 200


def test_is_ready_based_on_primary_window():
    engine = _engine(min_samples=6, primary="5min")
    buffer = RollingWindowBuffer([1, 2], max_samples=300)

    # 20 entries -> 1min ready (>=6) but 5min not (<30 min_samples).
    _push(buffer, 1, list(range(20)))
    _push(buffer, 2, list(range(20)))
    vector_low = engine._compute_vector("model_a", [1, 2], buffer)
    assert vector_low.windows["1min"].is_ready is True
    assert vector_low.is_ready is False  # 5min still short of 30 entries

    # Bring total to 30 entries -> 5min ready (each signal has 30 in tail).
    _push(buffer, 1, list(range(20, 30)))
    _push(buffer, 2, list(range(20, 30)))
    vector_ok = engine._compute_vector("model_a", [1, 2], buffer)
    assert vector_ok.windows["5min"].is_ready is True
    assert vector_ok.is_ready is True


def test_flat_key_format_and_no_none():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2], max_samples=300)
    for sid in (1, 2):
        _push(buffer, sid, list(range(30)))

    vector = engine._compute_vector("model_a", [1, 2], buffer)
    # At least one key of the documented shape.
    assert any(k.endswith("__5min__mean") for k in vector.features_flat)
    # None values are excluded entirely.
    assert None not in vector.features_flat.values()
    # Key format is exactly "{signal_id}__{window}__{feature}".
    for key in vector.features_flat:
        parts = key.split("__")
        assert len(parts) == 3
        assert parts[0].isdigit()
        assert parts[1] in _TEST_WINDOWS
        assert parts[2] in {
            "mean",
            "std",
            "trend",
            "roc",
            "min_val",
            "max_val",
            "last_val",
        }


def test_flatten_excludes_empty_signal():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2], max_samples=300)
    _push(buffer, 1, list(range(30)))
    # signal 2 has no data -> all None -> excluded.

    vector = engine._compute_vector("model_a", [1, 2], buffer)
    assert any(k.startswith("1__") for k in vector.features_flat)
    assert not any(k.startswith("2__") for k in vector.features_flat)


def test_has_bad_quality_flagged():
    engine = _engine()
    buffer = RollingWindowBuffer([1], max_samples=300)
    qualities = ["GOOD"] * 8 + ["STALE", "STALE"]
    _push(buffer, 1, list(range(10)), quality=qualities)

    sf = engine._compute_signal_features(1, buffer.get_window(1))
    assert sf.has_bad_quality is True


def test_on_tick_returns_all_models():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2, 3, 4], max_samples=300)
    for sid in (1, 2, 3, 4):
        _push(buffer, sid, list(range(30)))

    result = engine.on_tick(buffer)
    assert set(result.keys()) == {"model_a", "model_b"}
    assert all(isinstance(v, FeatureVector) for v in result.values())
    for v in result.values():
        assert isinstance(v.windows["1min"], WindowFeatures)


def test_on_tick_never_raises():
    engine = _engine()

    class BrokenBuffer:
        def get_last_n(self, signal_id, n):
            raise RuntimeError("boom")

        def get_window(self, signal_id):
            raise RuntimeError("boom")

    # Engine must swallow errors, computing empty features per signal.
    result = engine.on_tick(BrokenBuffer())
    # Buffer failures should never propagate; either an empty result or
    # vectors with zero-sample features per window are acceptable.
    if result:
        for v in result.values():
            for wf in v.windows.values():
                for sf in wf.signal_features.values():
                    assert sf.sample_count == 0


def test_summary_reports_per_window_readiness():
    engine = _engine()
    buffer = RollingWindowBuffer([1, 2, 3, 4], max_samples=300)
    for sid in (1, 2, 3, 4):
        _push(buffer, sid, list(range(30)))

    engine.on_tick(buffer)
    summary = engine.summary()
    assert "model_a" in summary
    assert "windows" in summary["model_a"]
    assert set(summary["model_a"]["windows"].keys()) == set(_TEST_WINDOWS.keys())
    entry = summary["model_a"]["windows"]["5min"]
    assert "is_ready" in entry and "ready_ratio" in entry
