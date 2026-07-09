"""Cause resolvers for Low-Production sub-analysis (Section 7.1).

Tries each resolver in YAML priority order and returns the first confident
match. Every backend-querying resolver catches its own exceptions and returns
None — a missing form/endpoint must never crash the tick.
"""

from __future__ import annotations

import logging

from state.low_production_models import CauseCandidate

logger = logging.getLogger(__name__)


def _op_gt(a, b):
    return a > b


def _op_lt(a, b):
    return a < b


def _op_gte(a, b):
    return a >= b


def _op_lte(a, b):
    return a <= b


_OPERATORS = {
    "gt": _op_gt,
    "lt": _op_lt,
    "gte": _op_gte,
    "lte": _op_lte,
}


class CauseResolver:
    """Resolve the most likely cause of a low-production phase."""

    def __init__(self, catalog: list[dict], config: dict, signal_client) -> None:
        self._config = config.get("cause_resolution", {})
        self._signal_client = signal_client
        self._catalog_map = {
            s["id"]: s for s in catalog if s.get("id") is not None
        }

    async def resolve(
        self, vector, window_key: str, run_id, state_history
    ) -> CauseCandidate | None:
        """Return the first confident cause match, or None."""
        for name in self._config.get("priority_order", []):
            try:
                candidate = await self._dispatch(
                    name, vector, window_key, run_id, state_history
                )
            except Exception as exc:
                logger.debug("Cause resolver '%s' failed: %s", name, exc)
                candidate = None
            if candidate is not None:
                return candidate
        return None

    async def _dispatch(
        self, name: str, vector, window_key: str, run_id, state_history
    ) -> CauseCandidate | None:
        conf = self._config.get(name, {})
        if name == "planned_slowdown":
            return await self._resolve_planned_slowdown(run_id, conf)
        if name == "phase_transition":
            return self._resolve_phase_transition(state_history, conf)
        if name == "material_problem":
            return await self._resolve_material_problem(run_id, conf)
        if name == "feeder_fault":
            return self._resolve_feeder_fault(vector, conf)
        if name == "pressure_instability":
            return self._resolve_pressure_instability(vector, conf)
        if name == "screen_nozzle_restriction":
            return self._resolve_screen_nozzle_restriction(vector, conf)
        if name == "material_change":
            return await self._resolve_material_change(run_id, conf)
        logger.debug("Unknown cause resolver '%s'", name)
        return None

    def _resolve_phase_transition(
        self, state_history, conf: dict
    ) -> CauseCandidate | None:
        lookback = int(conf.get("lookback_state_history", 3))
        transition_from = set(conf.get("transition_from_phases", []))
        if not state_history or lookback <= 0:
            return None
        # Exclude the current (most recent) entry; inspect the preceding ones.
        prior = list(state_history)[-(lookback + 1) : -1]
        if not prior:
            prior = list(state_history)[:-1] if len(state_history) > 1 else []
        for entry in reversed(prior):
            phase = entry.get("phase_name")
            if phase in transition_from:
                return CauseCandidate(
                    cause_name="phase_transition",
                    confidence=0.6,
                    is_planned=False,
                    evidence=f"preceded by {phase}",
                )
        return None

    async def _resolve_planned_slowdown(
        self, run_id, conf: dict
    ) -> CauseCandidate | None:
        if not conf.get("enabled", True):
            return None
        try:
            events = await self._signal_client.get_production_events(
                run_id, lookback_minutes=conf.get("lookback_minutes", 20)
            )
        except Exception:
            return None
        marker = conf.get("level_2_marker", "Low Production")
        keyword = str(conf.get("planned_reason_keyword", "planned")).lower()
        for event in events or []:
            if event.get("level_2") == marker:
                reason = (event.get("reason") or "").lower()
                is_planned = keyword in reason
                return CauseCandidate(
                    cause_name="planned_slowdown",
                    confidence=0.9,
                    is_planned=is_planned,
                    evidence=f"event_id={event.get('id')}",
                )
        return None

    async def _resolve_material_problem(
        self, run_id, conf: dict
    ) -> CauseCandidate | None:
        if not conf.get("enabled", True):
            return None
        try:
            events = await self._signal_client.get_material_behavior_events(
                run_id, lookback_minutes=conf.get("lookback_minutes", 15)
            )
        except Exception:
            return None
        if events:
            return CauseCandidate(
                cause_name="material_problem",
                confidence=0.7,
                is_planned=False,
                evidence=f"recent_event_id={events[0].get('id')}",
            )
        return None

    def _resolve_feeder_fault(self, vector, conf: dict) -> CauseCandidate | None:
        if vector is None:
            return None
        wf = vector.windows.get(conf.get("window_key", "5min"))
        if wf is None:
            return None
        group = conf.get("signal_group", "feeders")
        role = conf.get("signal_role", "error")
        op = conf.get("operator", "gt")
        threshold = conf.get("threshold", 0.0)
        for sid, sf in wf.signal_features.items():
            meta = self._catalog_map.get(sid, {})
            if meta.get("signal_group") != group:
                continue
            if meta.get("signal_role") != role:
                continue
            if sf.last_val is None:
                continue
            if self._apply_op(sf.last_val, op, threshold):
                return CauseCandidate(
                    cause_name="feeder_fault",
                    confidence=0.8,
                    is_planned=False,
                    evidence=f"signal_id={sid} val={sf.last_val}",
                )
        return None

    def _resolve_pressure_instability(
        self, vector, conf: dict
    ) -> CauseCandidate | None:
        if vector is None:
            return None
        wf = vector.windows.get(conf.get("window_key", "15min"))
        if wf is None:
            return None
        feature = conf.get("feature", "std")
        threshold = float(conf.get("threshold", 10.0))
        for group in conf.get("groups", []):
            vals = []
            for sid, sf in wf.signal_features.items():
                meta = self._catalog_map.get(sid, {})
                if meta.get("signal_group") != group:
                    continue
                value = getattr(sf, feature, None)
                if value is not None:
                    vals.append(float(value))
            if vals and max(vals) > threshold:
                return CauseCandidate(
                    cause_name="pressure_instability",
                    confidence=0.6,
                    is_planned=False,
                    evidence=f"group={group} max_std={max(vals):.2f}",
                )
        return None

    def _resolve_screen_nozzle_restriction(
        self, vector, conf: dict
    ) -> CauseCandidate | None:
        if not conf.get("enabled", False):
            return None
        # Placeholder until inlet/outlet tags are confirmed (matches anomaly).
        return None

    async def _resolve_material_change(
        self, run_id, conf: dict
    ) -> CauseCandidate | None:
        if not conf.get("enabled", True):
            return None
        try:
            events = await self._signal_client.get_production_events(
                run_id, lookback_minutes=conf.get("lookback_minutes", 30)
            )
        except Exception:
            return None
        for event in events or []:
            combined = (
                f"{event.get('level_1', '')}{event.get('level_2', '')}"
            ).lower()
            if "material" in combined:
                return CauseCandidate(
                    cause_name="material_change",
                    confidence=0.5,
                    is_planned=False,
                    evidence=f"event_id={event.get('id')}",
                )
        return None

    @staticmethod
    def _apply_op(val, op, threshold) -> bool:
        func = _OPERATORS.get(op)
        if func is None:
            return False
        return func(val, threshold)
