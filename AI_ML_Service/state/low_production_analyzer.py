"""Low-Production Cause & Severity sub-analysis (Section 7.1).

Extension of Process State — not a separate capability. Fires only when
``phase_name == "low_production"``. All thresholds live in
``low_production_config.yaml``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from core.config import get_settings
from state.cause_resolver import CauseResolver
from state.low_production_models import LowProductionResult

logger = logging.getLogger(__name__)


def _load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


class LowProductionAnalyzer:
    """Compute severity, duration, and cause while in low_production."""

    def __init__(
        self,
        catalog: list[dict],
        config_path: str | Path,
        signal_client,
        prediction_writer,
    ) -> None:
        self._config = _load_config(config_path)
        self._catalog_map = {
            s["id"]: s for s in catalog if s.get("id") is not None
        }
        self._signal_client = signal_client
        self._writer = prediction_writer
        self._cause_resolver = CauseResolver(
            catalog, self._config, signal_client
        )
        self.duration_ticks = 0
        self.last_result: LowProductionResult | None = None

    async def on_tick(
        self,
        vector,
        phase_result,
        poll_count: int,
        state_history,
        window_key: str | None = None,
    ) -> None:
        """Analyze low production when the current phase matches."""
        try:
            settings = get_settings()
            if window_key is None:
                window_key = settings.PRIMARY_WINDOW_KEY

            if phase_result is None or phase_result.phase_name != "low_production":
                self.duration_ticks = 0
                return

            self.duration_ticks += 1
            min_ticks = int(
                self._config.get("duration", {}).get(
                    "min_duration_ticks_for_alert", 1
                )
            )
            if self.duration_ticks < min_ticks:
                return

            severity = self._compute_severity(vector, window_key)
            if severity is None:
                return

            run_id = await self._writer.get_active_run_id()
            if run_id is None:
                return

            cause = await self._cause_resolver.resolve(
                vector, window_key, run_id, state_history
            )

            duration_sec = (
                self.duration_ticks
                * settings.PREDICT_EVERY_N_POLLS
                * settings.POLL_INTERVAL_SEC
            )

            result = LowProductionResult(
                severity=round(severity, 4),
                duration_ticks=self.duration_ticks,
                duration_sec=float(duration_sec),
                cause_name=cause.cause_name if cause else "unknown",
                confidence=cause.confidence if cause else 0.0,
                is_planned=cause.is_planned if cause else False,
                evidence=cause.evidence if cause else "no resolver matched",
            )
            self.last_result = result

            await self._writer.write_low_production(
                result, vector, run_id, window_key
            )
            logger.info(
                "[LOW_PROD] severity=%s duration_sec=%s cause=%s planned=%s",
                result.severity,
                result.duration_sec,
                result.cause_name,
                result.is_planned,
            )
        except Exception as exc:  # on_tick must never raise
            logger.error("LowProductionAnalyzer.on_tick failed: %s", exc)

    def _compute_severity(self, vector, window_key: str) -> float | None:
        cfg = self._config.get("severity", {})
        if vector is None:
            return None
        wf = vector.windows.get(window_key)
        if wf is None:
            return None

        group = cfg.get("throughput_signal_group", "feeders")
        actual_role = cfg.get("actual_role", "actual")
        setpoint_role = cfg.get("setpoint_role", "setpoint")
        clamp_min = float(cfg.get("clamp_min", 0.0))
        clamp_max = float(cfg.get("clamp_max", 1.0))

        actual_vals = []
        setpoint_vals = []
        for sid, sf in wf.signal_features.items():
            meta = self._catalog_map.get(sid, {})
            if meta.get("signal_group") != group or sf.last_val is None:
                continue
            role = meta.get("signal_role")
            if role == actual_role:
                actual_vals.append(float(sf.last_val))
            elif role == setpoint_role:
                setpoint_vals.append(float(sf.last_val))

        if not actual_vals or not setpoint_vals:
            return None

        actual_mean = sum(actual_vals) / len(actual_vals)
        setpoint_mean = sum(setpoint_vals) / len(setpoint_vals)
        if setpoint_mean == 0:
            return None

        severity = 1.0 - (actual_mean / setpoint_mean)
        return max(clamp_min, min(clamp_max, severity))

    def get_status(self) -> dict:
        if self.last_result is None:
            return {"status": "not_in_low_production"}
        r = self.last_result
        return {
            "severity": r.severity,
            "duration_ticks": r.duration_ticks,
            "duration_sec": r.duration_sec,
            "cause_name": r.cause_name,
            "confidence": r.confidence,
            "is_planned": r.is_planned,
            "evidence": r.evidence,
        }
