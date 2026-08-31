# SUNPOR — Predictive AI for Extrusion Production

SUNPOR is an industrial platform for **extrusion line monitoring, production-run lifecycle, operator capture, and AI-assisted process insight**. Live WinCC signals flow into a TimescaleDB-backed backend; services detect production activity, classify process state, surface anomalies, and help operators record what happens on the line.

---

## What the platform does

1. **Ingest live plant signals** (WinCC tags via MQTT) into a signal catalog and timeseries store  
2. **Detect production** from sensors and open/close **production runs** automatically  
3. **Classify process state** (startup, stable, low production, cleaning, faults, …) and write predictions for the active run  
4. **Detect early anomalies** and low-production causes against calibrated rules  
5. **Support operators** with assist suggestions, issue reporting, and structured input forms  
6. **Present everything** in a web UI: live sensors, production runs, forms, and AI views  

---

## How data flows

```
WinCC / plant tags
       │
       ▼
 MQTT broker  ──►  MQTT subscriber  ──►  Backend (signal_catalog + timeseries)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
           productionController         AI_ML_Service          Operator Assist
           (auto create/complete         (process state,         (rule-based
            production runs)              anomalies, LP)           suggestions)
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              ▼
                                    Backend APIs + PostgreSQL
                                              │
                                              ▼
                                         Frontend UI
```

Production runs are the central timeline. Sensor detection can create a `RUNNING` run before the operator fills the form; AI features attach predictions and insights to that run; operators enrich it with events, quality, and material notes.

---

## Main components

### Backend (`backend/`)
FastAPI + SQLAlchemy + Alembic + PostgreSQL/TimescaleDB.  
Owns master data (companies, lines, materials, shifts, users), **signal catalog** (each WinCC tag linked to `company_id` / `production_line_id`), timeseries, **production runs**, operator entries, ML prediction storage, auth (JWT), and RBAC.

### Frontend (`frontend/`)
React (Vite) operator and plant UI: live sensor views, production-run dashboards, operator home / assist flows, input forms (questionnaire-style hub + recent entries), and admin/master-data screens. German locale support for operator-facing text.

### productionController (`productionController/`)
Multi-company / multi-line service that:

- Discovers companies and active production lines  
- Uses only signals linked to each line in `signal_catalog`  
- Evaluates production-active rules (status, feeders, extruder/meltpump, melt pressure)  
- **Creates** `RUNNING` production runs when sensors stay active (debounced)  
- **Completes** them when sensors stay inactive  
- **Syncs** every tick with the backend so external COMPLETED/RUNNING changes are respected  

Auto-created runs carry a German comment that they were sensor-detected and await operator confirmation.

### AI_ML_Service (`AI_ML_Service/`)
Polls live signals for the active run, builds feature windows, and:

- Runs a **process-state** rule engine (phases such as stable / low production / cleaning / faults)  
- Writes predictions back to the backend for the current production run  
- Runs **early anomaly** detection (including absolute safety / Stage 0 style checks)  
- Analyzes **low-production** cause and severity when that phase is active  

Depends on an existing production run (so productionController and AI_ML complement each other).

### Operator Assist (`operator_assist_service/`)
Lightweight rule service that analyzes current context and returns operator-facing suggestions. Shares process-rule concepts with AI_ML; the frontend/backend call it during assist flows.

### MQTT + simulator (`mqqt+simulator/`)
Mosquitto broker, a subscriber that writes plant/simulated tags into the backend, and optional simulators for development and demos without live WinCC.

### Docs (`Docs/`)
Specifications, client briefs, operator-form overview, and related project documentation.

---

## Production run lifecycle (core idea)

| Phase | Who acts | Result |
|-------|----------|--------|
| Sensors show line producing | productionController | `POST` production run → `RUNNING` |
| Operator works the shift | Frontend + forms | Recipe, order, events, quality, comments |
| Line still producing | AI_ML_Service | Process state + anomalies on that run |
| Sensors show line stopped | productionController | `PUT` run → `COMPLETED` + `end_time` |
| Operator completes early | Backend / UI | Controller notices COMPLETED next poll; if sensors still active, opens a **new** run |

Only one `RUNNING` run is allowed per production line.

---

## Domain model (high level)

- **Company** → **Production lines** (e.g. Extrusion E10)  
- **Signal catalog** — WinCC tags with `signal_group` / `signal_role`, scoped to company + line  
- **Signal timeseries** — latest and historical scaled values + quality  
- **Production run** — `RUNNING` / `COMPLETED`, tied to company, line, shift, operator, material  
- **Operator entries** — unified questionnaire payloads for new forms  
- **ML predictions / process state** — attached to the active run  

---

## Design principles

- **Sensors bootstrap the run**; operators confirm and enrich — AI does not invent the run from ML state alone  
- **Line-scoped signals** — detection and AI features use catalog links, not hard-coded tag lists  
- **Rules are tunable in YAML** (productionController and AI_ML) without rewriting application code  
- **Services are separable** — backend is the system of record; controllers and ML poll via APIs  

---

## Repository map

| Path | Role |
|------|------|
| `backend/` | APIs, models, auth, Timescale/Postgres |
| `frontend/` | Operator & plant web application |
| `productionController/` | Auto production-run create/complete |
| `AI_ML_Service/` | Process state, anomalies, low-production analysis |
| `operator_assist_service/` | Operator suggestion rules |
| `mqqt+simulator/` | Signal ingestion path + simulators |
| `Docs/` | Specs and project documentation |
| `database/` | DB-related assets |
| `DataAnalysis/` | Offline / analysis notebooks and helpers |

---

SUNPOR turns live extrusion signals into a continuous production timeline, then layers operator knowledge and AI insight on top of that timeline.
