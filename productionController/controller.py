"""productionController entry point — multi-company / multi-line poll loop."""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import httpx

# Allow running as `python controller.py` from productionController/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from auth_client import AuthClient
from backend_client import BackendClient
from config import Settings, load_pc_config
from orchestrator import ProductionOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("productionController")


async def main() -> None:
    settings = Settings()
    pc_config = load_pc_config(settings.CONFIG_PATH)

    async with httpx.AsyncClient(timeout=30.0) as http:
        auth = AuthClient(settings, http)
        await auth.login()

        client = BackendClient(auth, settings, pc_config, http_client=http)

        operator_id = settings.OPERATOR_ID or auth.authenticated_user_id
        if operator_id is None:
            raise RuntimeError(
                "operator_id unresolved — set OPERATOR_ID or ensure /auth/me returns id"
            )
        material_type_id = settings.DEFAULT_MATERIAL_TYPE_ID or (
            await client.resolve_default_material_type_id()
        )

        orchestrator = ProductionOrchestrator(
            client,
            pc_config,
            operator_id=int(operator_id),
            default_material_type_id=int(material_type_id),
        )
        await orchestrator.startup()
        for status in orchestrator.get_status():
            logger.info("Initial line status: %s", status)

        poll_sec = int(pc_config.get("poll_interval_sec", 5))
        logger.info(
            "Polling every %ss across %d production line(s)",
            poll_sec,
            orchestrator.line_count,
        )

        while True:
            try:
                await orchestrator.on_tick()
            except Exception as exc:  # never crash the outer loop
                logger.exception("orchestrator tick failed: %s", exc)
            await asyncio.sleep(poll_sec)


if __name__ == "__main__":
    asyncio.run(main())
