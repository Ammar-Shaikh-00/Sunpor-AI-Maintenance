"""Debounced production-run start/stop from live sensor signals.

Creates a RUNNING production_run when sensors show the line is producing,
before the operator confirms/fills the form. Completes the run when sensors
show production has stopped.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"


class RunManager:
    """Creates/completes production runs from sensor-based activity."""

    def __init__(self, backend_client, pc_config: dict, cached_ids: dict) -> None:
        # cached_ids keys: company_id, production_line_id, operator_id,
        # default_material_type_id
        self.backend_client = backend_client
        self.pc_config = pc_config
        self.cached_ids = cached_ids
        self.state = RunState.IDLE
        self.active_run_id: Optional[int] = None
        self._start_ticks = 0
        self._stop_ticks = 0
        self.last_detection: dict | None = None

    async def startup(self) -> None:
        # Warm catalog cache
        if hasattr(self.backend_client, "fetch_catalog"):
            await self.backend_client.fetch_catalog()

        if not self.pc_config.get("adopt_existing_run_on_startup", True):
            return
        existing = await self.backend_client.get_active_run(
            self.cached_ids["production_line_id"]
        )
        if existing:
            self.state = RunState.RUNNING
            self.active_run_id = int(existing["id"])
            logger.info(
                "Adopted existing RUNNING production run %s on startup",
                self.active_run_id,
            )

    async def on_tick(self) -> None:
        is_active, info = await self.backend_client.is_production_active()
        self.last_detection = info

        if info.get("reason") == "no_latest_signals":
            logger.info("no latest signal snapshot yet")
            return

        start_n = int(self.pc_config.get("start_debounce_ticks", 3))
        stop_n = int(self.pc_config.get("stop_debounce_ticks", 5))

        logger.info(
            "sensor tick: active=%s passed=%s/%s",
            is_active,
            info.get("passed"),
            info.get("evaluated"),
        )

        if self.state == RunState.IDLE:
            if is_active:
                self._start_ticks += 1
                self._stop_ticks = 0
                if self._start_ticks >= start_n:
                    await self._create_run()
            else:
                self._start_ticks = 0
        elif self.state == RunState.RUNNING:
            if not is_active:
                self._stop_ticks += 1
                self._start_ticks = 0
                if self._stop_ticks >= stop_n:
                    await self._complete_run()
            else:
                self._stop_ticks = 0

    async def _create_run(self) -> None:
        shift_id = await self.backend_client.resolve_current_shift_id()
        comment = self.pc_config.get("auto_run_comment")
        result = await self.backend_client.create_production_run(
            company_id=self.cached_ids["company_id"],
            production_line_id=self.cached_ids["production_line_id"],
            start_time=_utcnow(),
            material_type_id=self.cached_ids["default_material_type_id"],
            shift_id=shift_id,
            operator_id=self.cached_ids["operator_id"],
            is_trial=bool(self.pc_config.get("is_trial", False)),
            comment=comment,
        )
        if result:
            self.active_run_id = int(result["id"])
            self.state = RunState.RUNNING
            self._start_ticks = 0
            logger.info(
                "Auto-created production run %s from sensors, shift=%s",
                self.active_run_id,
                shift_id,
            )
            return

        # 400 conflict: another RUNNING run exists — adopt it
        existing = await self.backend_client.get_active_run(
            self.cached_ids["production_line_id"]
        )
        if existing:
            self.active_run_id = int(existing["id"])
            self.state = RunState.RUNNING
            self._start_ticks = 0
            logger.info(
                "Adopted existing RUNNING run %s after 400 conflict",
                self.active_run_id,
            )

    async def _complete_run(self) -> None:
        run_id = self.active_run_id
        if run_id is None:
            self.state = RunState.IDLE
            self._stop_ticks = 0
            return
        await self.backend_client.complete_production_run(
            run_id=run_id,
            end_time=_utcnow(),
        )
        logger.info("Auto-completed production run %s (sensors inactive)", run_id)
        self.active_run_id = None
        self.state = RunState.IDLE
        self._stop_ticks = 0

    def get_status(self) -> dict:
        return {
            "state": self.state,
            "active_run_id": self.active_run_id,
            "start_ticks": self._start_ticks,
            "stop_ticks": self._stop_ticks,
            "last_detection": self.last_detection,
        }
