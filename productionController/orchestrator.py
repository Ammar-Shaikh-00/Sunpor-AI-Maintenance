"""Multi-company / multi-line orchestrator for productionController.

Discovers all companies and their production lines from the backend, keeps one
RunManager per line that has signal_catalog WinCC links, and polls them each
cycle from a shared sensor/run snapshot.
"""

from __future__ import annotations

import asyncio
import logging
import time

from backend_client import BackendClient, LineTarget
from run_manager import RunManager

logger = logging.getLogger(__name__)


class ProductionOrchestrator:
    """Owns one RunManager per managed production line."""

    def __init__(
        self,
        backend_client: BackendClient,
        pc_config: dict,
        *,
        operator_id: int,
        default_material_type_id: int,
    ) -> None:
        self.backend_client = backend_client
        self.pc_config = pc_config
        self.operator_id = int(operator_id)
        self.default_material_type_id = int(default_material_type_id)
        self.managers: dict[int, RunManager] = {}
        self._last_topology_refresh: float = 0.0

    @property
    def line_count(self) -> int:
        return len(self.managers)

    def get_status(self) -> list[dict]:
        return [m.get_status() for m in self.managers.values()]

    async def startup(self) -> None:
        await self.refresh_topology(force=True)
        if not self.managers:
            logger.warning(
                "No managed production lines discovered — "
                "check companies, active lines, and signal_catalog links"
            )

    async def refresh_topology(self, *, force: bool = False) -> None:
        refresh_sec = float(self.pc_config.get("topology_refresh_sec", 300))
        now = time.monotonic()
        if (
            not force
            and self._last_topology_refresh
            and (now - self._last_topology_refresh) < refresh_sec
        ):
            return

        targets = await self.backend_client.discover_managed_lines()
        wanted = {t.production_line_id: t for t in targets}

        # Remove managers for lines that disappeared / filtered out
        for lid in list(self.managers):
            if lid not in wanted:
                logger.info(
                    "Removing manager for line #%s (no longer discovered)", lid
                )
                del self.managers[lid]

        # Add managers for new lines
        for lid, target in wanted.items():
            if lid in self.managers:
                continue
            manager = self._build_manager(target)
            await manager.startup()
            self.managers[lid] = manager
            logger.info(
                "Managing line %s (%d catalog signals)",
                target.label,
                target.signal_count,
            )

        self._last_topology_refresh = now
        logger.info("Topology ready: %d line manager(s)", len(self.managers))

    def _build_manager(self, target: LineTarget) -> RunManager:
        cached_ids = {
            "company_id": target.company_id,
            "company_name": target.company_name,
            "production_line_id": target.production_line_id,
            "production_line_name": target.production_line_name,
            "operator_id": self.operator_id,
            "default_material_type_id": self.default_material_type_id,
        }
        return RunManager(self.backend_client, self.pc_config, cached_ids)

    async def on_tick(self) -> None:
        await self.refresh_topology(force=False)

        if not self.managers:
            logger.warning("No line managers — skipping tick")
            return

        await self.backend_client.begin_poll_snapshot()
        try:
            await asyncio.gather(
                *(self._safe_line_tick(mgr) for mgr in self.managers.values())
            )
        finally:
            self.backend_client.end_poll_snapshot()

    async def _safe_line_tick(self, manager: RunManager) -> None:
        try:
            await manager.on_tick()
        except Exception:
            logger.exception("[%s] on_tick failed", manager.label)
