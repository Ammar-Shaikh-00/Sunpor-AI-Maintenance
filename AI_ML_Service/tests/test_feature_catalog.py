"""Unit tests for the feature catalog (signal <-> model mapping)."""

from features.feature_catalog import (
    GROUP_MODEL_MAP,
    MODEL_ANOMALY,
    MODEL_GRANULATOR,
    MODEL_LOW_PRODUCTION,
    MODEL_MATERIAL_BEHAVIOR,
    MODEL_NOZZLE_SCREEN,
    MODEL_PREDICTIVE_QUALITY,
    MODEL_PROCESS_STATE,
    FeatureCatalog,
)


def _id_for_group(catalog: list[dict], group: str) -> int:
    return next(s["id"] for s in catalog if s["signal_group"] == group)


def test_all_ten_groups_mapped():
    expected = {
        "heating_zones",
        "feeders",
        "screen_changer",
        "process_water",
        "granulator",
        "melt_pressure",
        "offspec",
        "pentane_nitrogen",
        "extruder_meltpump",
        "status",
    }
    assert expected == set(GROUP_MODEL_MAP.keys())


def test_models_for_signal_by_group(mock_catalog):
    fc = FeatureCatalog(mock_catalog)

    sid = _id_for_group(mock_catalog, "granulator")
    assert set(fc.get_models_for_signal(sid)) == {MODEL_GRANULATOR, MODEL_ANOMALY}

    sid = _id_for_group(mock_catalog, "pentane_nitrogen")
    assert set(fc.get_models_for_signal(sid)) == {
        MODEL_MATERIAL_BEHAVIOR,
        MODEL_ANOMALY,
    }

    sid = _id_for_group(mock_catalog, "melt_pressure")
    assert set(fc.get_models_for_signal(sid)) == {
        MODEL_PROCESS_STATE,
        MODEL_NOZZLE_SCREEN,
        MODEL_PREDICTIVE_QUALITY,
    }


def test_signals_for_model(mock_catalog):
    fc = FeatureCatalog(mock_catalog)

    # process_state is fed by heating_zones, feeders, melt_pressure,
    # extruder_meltpump, status -> 5 groups, one signal each in the mock.
    process_signals = fc.get_signals_for_model(MODEL_PROCESS_STATE)
    assert len(process_signals) == 5

    low_prod = fc.get_signals_for_model(MODEL_LOW_PRODUCTION)
    # feeders, extruder_meltpump, status
    assert len(low_prod) == 3


def test_summary_counts(mock_catalog):
    fc = FeatureCatalog(mock_catalog)
    summary = fc.summary()

    assert summary[MODEL_PROCESS_STATE] == 5
    assert summary[MODEL_LOW_PRODUCTION] == 3
    assert summary[MODEL_GRANULATOR] == 1
    assert summary[MODEL_MATERIAL_BEHAVIOR] == 1
    assert summary[MODEL_NOZZLE_SCREEN] == 2  # screen_changer + melt_pressure
    # anomaly: heating, feeders, screen_changer, process_water, granulator,
    # offspec, pentane_nitrogen, extruder_meltpump -> 8
    assert summary[MODEL_ANOMALY] == 8


def test_unknown_signal_returns_empty(mock_catalog):
    fc = FeatureCatalog(mock_catalog)
    assert fc.get_models_for_signal(9999) == []
    assert fc.get_signals_for_model("no_such_model") == []
