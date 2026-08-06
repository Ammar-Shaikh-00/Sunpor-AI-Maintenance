# productionController

Multi-company / multi-line service that polls live WinCC sensor signals from the
SUNPOR backend and **auto-creates / completes production runs** before the
operator fills the form.

For **each company** → **each active production line** that has rows in
`signal_catalog` (linked by `production_line_id`):

- **Start:** line sensors show producing → create a `RUNNING` production run
- **Stop:** sensors show stopped → set the run to `COMPLETED`
- **Sync:** every tick, adopt an existing `RUNNING` run or notice external `COMPLETED`

Detection does **not** use ML `process_state`. It uses catalog group/role + latest
timeseries, scoped per line via `signal_catalog.production_line_id`.

---

## Requirements

- Python 3.10+
- Reachable SUNPOR backend API
- Backend user with access to companies, lines, signals, and production runs

---

## Setup

```powershell
cd productionController
python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`:

| Variable | Purpose |
|----------|---------|
| `BACKEND_URL` | Backend base URL (e.g. `http://192.168.100.24:8000`) |
| `PC_EMAIL` / `PC_PASSWORD` | Service login |
| `CONFIG_PATH` | YAML config (default `production_config.yaml`) |
| `OPERATOR_ID` | Optional — else from `GET /auth/me` |
| `DEFAULT_MATERIAL_TYPE_ID` | Optional — else first material type |
| `COMPANY_ID` | Optional filter — only this company |
| `PRODUCTION_LINE_ID` | Optional filter — only this line |

Discovery / debounce / thresholds: `production_config.yaml`.

---

## Run

```powershell
cd productionController
python controller.py
```

Stop with `Ctrl+C`.

### Tests

```powershell
cd productionController
python -m pytest tests/ -v
```

---

## How it scales

Each poll cycle (`poll_interval_sec`, default **5s**):

1. (Periodically) discover topology:
   - `GET /companies` (all pages)
   - `GET /production-lines` (all pages)
   - Keep lines that are `active` and have `signal_catalog` rows for that `production_line_id`
2. Load a **shared snapshot** once:
   - `GET /signal-catalog`
   - `GET /signal-timeseries/latest`
   - `GET /production-runs`
3. For **each managed line in parallel**:
   - Evaluate only that line’s catalog signals
   - Sync RUNNING / COMPLETED for that line
   - Debounce create / complete

One line failing does not stop the others.

Optional YAML filters (`company_ids`, `company_names`, `production_line_ids`,
`production_line_names`) or env `COMPANY_ID` / `PRODUCTION_LINE_ID` narrow scope.
Empty filters = **all** companies and lines.

---

## Detection rules (per line)

Default conditions (all must pass) — mean of matching `value_scaled`:

- `status` ≥ 1  
- `feeders` / `actual` ≥ 50  
- `extruder_meltpump` / `actual` ≥ 15  
- `melt_pressure` / `actual` ≥ 40  

Debounce: **3** active ticks → create; **5** inactive ticks → complete.

Completed runs cannot be reopened by the backend API. If sensors stay active after
an external complete, a **new** RUNNING run is created.

---

## Backend APIs used

### Auth

| Method | Path | When |
|--------|------|------|
| `POST` | `/auth/login` | Startup / 401 retry |
| `GET` | `/auth/me` | Resolve `operator_id` |
| `POST` | `/auth/refresh` | Token refresh |

### Discovery

| Method | Path | When |
|--------|------|------|
| `GET` | `/companies` | List all companies (paginated) |
| `GET` | `/production-lines` | List all lines (paginated) |
| `GET` | `/material-types` | Default material type |
| `GET` | `/shifts` | Resolve `shift_id` by time-of-day |
| `GET` | `/signal-catalog` | Map signals → `company_id` / `production_line_id` / group / role |

### Every poll (shared snapshot)

| Method | Path | When |
|--------|------|------|
| `GET` | `/signal-catalog` | Cached; refreshed on topology refresh |
| `GET` | `/signal-timeseries/latest` | Live values for all WinCC tags |
| `GET` | `/production-runs` | Sync RUNNING runs per line |

### Per line actions

| Method | Path | When |
|--------|------|------|
| `GET` | `/production-runs/{id}` | Confirm status if tracked run disappears |
| `POST` | `/production-runs` | Create `RUNNING` for that company + line |
| `PUT` | `/production-runs/{id}` | Complete (`COMPLETED` + `end_time`) |

---

## Layout

```
productionController/
  controller.py              # Entry point
  orchestrator.py            # Multi-line discovery + parallel ticks
  auth_client.py
  backend_client.py          # HTTP + snapshot + discovery
  production_detector.py     # Line-scoped sensor rules
  run_manager.py             # Debounce per line
  config.py
  production_config.yaml
  requirements.txt
  .env.example
  tests/
```

---

## Notes

- Only one `RUNNING` run per line is allowed by the backend.
- Lines with **no** `signal_catalog` rows are skipped (`skip_lines_without_signals`).
- Topology re-discovery default: every **300s** (`topology_refresh_sec`).
- Do not commit `.env`. Use `.env.example` as the template.
