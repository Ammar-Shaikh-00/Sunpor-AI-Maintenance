"""Debounced production-run start/stop for a single production line.

Creates a RUNNING production_run when sensors for this line show producing,
before the operator confirms/fills the form. Completes the run when sensors
show production has stopped.

After every sensor check, syncs with the backend production run for the line
so external COMPLETED (or newly created RUNNING) runs are reflected immediately.
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
    """Creates/completes production runs for one production line."""

    def __init__(self, backend_client, pc_config: dict, cached_ids: dict) -> None:
        # cached_ids: company_id, company_name, production_line_id,
        # production_line_name, operator_id, default_material_type_id
        self.backend_client = backend_client
        self.pc_config = pc_config
        self.cached_ids = cached_ids
        self.state = RunState.IDLE
        self.active_run_id: Optional[int] = None
        self._start_ticks = 0
        self._stop_ticks = 0
        self.last_detection: dict | None = None

    @property
    def line_id(self) -> int:
        return int(self.cached_ids["production_line_id"])

    @property
    def label(self) -> str:
        company = self.cached_ids.get("company_name") or self.cached_ids["company_id"]
        line = (
            self.cached_ids.get("production_line_name")
            or self.cached_ids["production_line_id"]
        )
        return f"{company}/{line}#{self.line_id}"

    async def startup(self) -> None:
        if not self.pc_config.get("adopt_existing_run_on_startup", True):
            return
        existing = await self.backend_client.get_active_run(self.line_id)
        if existing:
            self.state = RunState.RUNNING
            self.active_run_id = int(existing["id"])
            logger.info(
                "[%s] Adopted existing RUNNING production run %s on startup",
                self.label,
                self.active_run_id,
            )

    async def on_tick(self) -> None:
        is_active, info = await self.backend_client.is_production_active(self.line_id)
        self.last_detection = info

        if info.get("reason") in ("no_latest_signals", "no_signals_for_line"):
            logger.info("[%s] %s", self.label, info.get("reason"))
            return

        await self._sync_run_from_backend()

        start_n = int(self.pc_config.get("start_debounce_ticks", 3))
        stop_n = int(self.pc_config.get("stop_debounce_ticks", 5))

        logger.info(
            "[%s] sensor tick: active=%s passed=%s/%s state=%s run_id=%s",
            self.label,
            is_active,
            info.get("passed"),
            info.get("evaluated"),
            self.state.value,
            self.active_run_id,
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

    async def _sync_run_from_backend(self) -> None:
        active = await self.backend_client.get_active_run(self.line_id)

        if active:
            run_id = int(active["id"])
            if self.state != RunState.RUNNING or self.active_run_id != run_id:
                logger.info(
                    "[%s] Synced RUNNING production run %s",
                    self.label,
                    run_id,
                )
            self.state = RunState.RUNNING
            self.active_run_id = run_id
            self._start_ticks = 0
            return

        if self.state == RunState.RUNNING:
            tracked_id = self.active_run_id
            status = "unknown"
            if tracked_id is not None and hasattr(
                self.backend_client, "get_production_run"
            ):
                tracked = await self.backend_client.get_production_run(tracked_id)
                if tracked:
                    status = str(tracked.get("status", "unknown"))
                else:
                    status = "missing"
            logger.info(
                "[%s] Run no longer RUNNING (tracked_id=%s status=%s); IDLE",
                self.label,
                tracked_id,
                status,
            )
            self.state = RunState.IDLE
            self.active_run_id = None
            self._stop_ticks = 0
            self._start_ticks = 0

    async def _create_run(self) -> None:
        existing = await self.backend_client.get_active_run(self.line_id)
        if existing:
            self.active_run_id = int(existing["id"])
            self.state = RunState.RUNNING
            self._start_ticks = 0
            logger.info(
                "[%s] Adopted existing RUNNING run %s before create",
                self.label,
                self.active_run_id,
            )
            return

        shift_id = await self.backend_client.resolve_current_shift_id()
        comment = self.pc_config.get("auto_run_comment")
        result = await self.backend_client.create_production_run(
            company_id=self.cached_ids["company_id"],
            production_line_id=self.line_id,
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
                "[%s] Auto-created production run %s, shift=%s",
                self.label,
                self.active_run_id,
                shift_id,
            )
            return

        existing = await self.backend_client.get_active_run(self.line_id)
        if existing:
            self.active_run_id = int(existing["id"])
            self.state = RunState.RUNNING
            self._start_ticks = 0
            logger.info(
                "[%s] Adopted existing RUNNING run %s after 400 conflict",
                self.label,
                self.active_run_id,
            )

    async def _complete_run(self) -> None:
        run_id = self.active_run_id
        if run_id is None:
            self.state = RunState.IDLE
            self._stop_ticks = 0
            return

        if hasattr(self.backend_client, "get_production_run"):
            current = await self.backend_client.get_production_run(run_id)
            if current and str(current.get("status")) == "COMPLETED":
                logger.info(
                    "[%s] Production run %s already COMPLETED; IDLE",
                    self.label,
                    run_id,
                )
                self.active_run_id = None
                self.state = RunState.IDLE
                self._stop_ticks = 0
                return

        await self.backend_client.complete_production_run(
            run_id=run_id,
            end_time=_utcnow(),
        )
        logger.info(
            "[%s] Auto-completed production run %s (sensors inactive)",
            self.label,
            run_id,
        )
        self.active_run_id = None
        self.state = RunState.IDLE
        self._stop_ticks = 0

    def get_status(self) -> dict:
        return {
            "label": self.label,
            "company_id": self.cached_ids["company_id"],
            "production_line_id": self.line_id,
            "state": self.state,
            "active_run_id": self.active_run_id,
            "start_ticks": self._start_ticks,
            "stop_ticks": self._stop_ticks,
            "last_detection": self.last_detection,
        }
