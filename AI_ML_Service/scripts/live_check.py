import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import httpx
from asgi_lifespan import LifespanManager

from core.auth_client import AuthClient
from core.config import get_settings
from ingestion.signal_client import SignalClient
from main import app


async def main():
    cur = {}
    hist = []
    async with LifespanManager(app):
        for i in range(18):
            await asyncio.sleep(12)
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://test", timeout=30
            ) as client:
                st = (await client.get("/ingestion/status")).json()
                fs = (await client.get("/features/summary")).json()
                cur = (await client.get("/state/current")).json()
                hist = (await client.get("/state/history")).json()
                bufs = list(st["buffer_snapshot"].values())
                ps = fs.get("process_state", {})
                phase = cur.get("phase_name", cur.get("status"))
                print(
                    f"t={i+1} polls={st['total_polls']} buf={max(bufs)} "
                    f"ready={ps.get('is_ready')} state={phase} hist={len(hist)}"
                )
                if cur.get("phase_name") and len(hist) >= 1 and i >= 14:
                    break

    s = get_settings()
    async with httpx.AsyncClient(timeout=30) as bc:
        auth = AuthClient(s, bc)
        await auth.login()
        sig = SignalClient(auth, bc)
        runs = await sig.fetch_production_runs(limit=10)
        print("RUNS", [(r.get("id"), r.get("status")) for r in runs])
        try:
            resp = await bc.get(
                f"{s.backend_base}/ml-predictions",
                headers=auth.get_headers(),
                params={"limit": 5},
            )
            print("ML_PRED_STATUS", resp.status_code)
            if resp.status_code == 200:
                print("ML_PREDS", resp.text[:800])
        except Exception as exc:
            print("ML_PRED_ERR", exc)

    print("FINAL_STATE", json.dumps(cur))
    if hist:
        print("LAST_HIST", json.dumps(hist[-1]))


if __name__ == "__main__":
    asyncio.run(main())
