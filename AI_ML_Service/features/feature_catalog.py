"""Feature catalog — maps signals to the ML models that consume them.

The mapping is driven entirely by ``signal_group`` from the live catalog, so
no individual signal name or id is ever hardcoded. Add a signal to a known
group in the backend catalog and it is automatically routed to the right
models.
"""

from __future__ import annotations

# ML model keys (must match prediction_type / model naming used elsewhere).
MODEL_PROCESS_STATE = "process_state"
MODEL_LOW_PRODUCTION = "low_production"
MODEL_ANOMALY = "anomaly"
MODEL_MATERIAL_BEHAVIOR = "material_behavior_risk"
MODEL_PREDICTIVE_QUALITY = "predictive_quality"
MODEL_GRANULATOR = "granulator_knife"
MODEL_NOZZLE_SCREEN = "nozzle_screen_pressure"

# signal_group -> models that consume that group.
GROUP_MODEL_MAP: dict[str, list[str]] = {
    "heating_zones": [MODEL_PROCESS_STATE, MODEL_ANOMALY],
    "feeders": [MODEL_PROCESS_STATE, MODEL_LOW_PRODUCTION, MODEL_ANOMALY],
    "screen_changer": [MODEL_NOZZLE_SCREEN, MODEL_ANOMALY],
    "process_water": [MODEL_ANOMALY],
    "granulator": [MODEL_GRANULATOR, MODEL_ANOMALY],
    "melt_pressure": [
        MODEL_PROCESS_STATE,
        MODEL_NOZZLE_SCREEN,
        MODEL_PREDICTIVE_QUALITY,
    ],
    "offspec": [MODEL_PREDICTIVE_QUALITY, MODEL_ANOMALY],
    "pentane_nitrogen": [MODEL_MATERIAL_BEHAVIOR, MODEL_ANOMALY],
    "extruder_meltpump": [MODEL_PROCESS_STATE, MODEL_LOW_PRODUCTION, MODEL_ANOMALY],
    "status": [MODEL_PROCESS_STATE, MODEL_LOW_PRODUCTION],
}


class FeatureCatalog:
    """Bidirectional mapping between signals and the ML models that use them."""

    def __init__(self, catalog: list[dict]) -> None:
        # model_key -> [signal_id, ...]
        self._model_to_signals: dict[str, list[int]] = {}
        # signal_id -> [model_key, ...]
        self._signal_to_models: dict[int, list[str]] = {}

        for signal in catalog:
            signal_id = signal.get("id")
            if signal_id is None:
                continue
            group = signal.get("signal_group")
            models = GROUP_MODEL_MAP.get(group, [])
            self._signal_to_models[signal_id] = list(models)
            for model_key in models:
                self._model_to_signals.setdefault(model_key, []).append(signal_id)

    def get_signals_for_model(self, model_key: str) -> list[int]:
        """Return the signal ids consumed by a given model."""
        return list(self._model_to_signals.get(model_key, []))

    def get_models_for_signal(self, signal_id: int) -> list[str]:
        """Return the models that consume a given signal."""
        return list(self._signal_to_models.get(signal_id, []))

    def summary(self) -> dict:
        """Return {model_key: signal_count} for startup logging."""
        return {
            model_key: len(signal_ids)
            for model_key, signal_ids in sorted(self._model_to_signals.items())
        }
