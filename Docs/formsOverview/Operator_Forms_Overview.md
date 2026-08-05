# Operator Forms – Brief Overview

**Purpose:** Help operators record production events and quality checks in a consistent way, so the data can later be used for analysis and AI.

**Source of truth:** `Docs/Operator_Input_Forms_Specification_EN.docx`  
**App entry:** Operator home (`/operator`) → category tiles → form or Recent Entries

---

## 1. Core concept (how storage works)

All **new** operator input forms share **one database table**:

| Table | Purpose |
|-------|---------|
| `operator_entries` | Stores every submitted operator form (dosing, extruder, quality, etc.) |

### Why one table?

Each form has many different questions. Instead of creating a separate table per form, we use:

1. **Shared columns** – for listing, filtering, and search (Recent Entries)
2. **`payload` (JSON)** – for all detailed answers of that form

So:

- **Recent Entries** can filter by category, time, run, status without reading every answer
- Each form can still keep its full questionnaire answers inside `payload`

### Related tables (lookups, not form bodies)

| Table | Used for |
|-------|----------|
| `production_runs` | Which production run the event belongs to |
| `users` | Who recorded / last updated the entry |
| `companies` | Company scope of the entry |
| `material_types` | Material names in dropdowns |
| `shifts` / `production_lines` | Context on the run (shift, line) |

> **Note:** Older forms (e.g. `/forms/extruder-events`, `/forms/material-behavior`) still use legacy tables such as `production_events`, `material_behavior_events`, `material_blocks`, `daily_quality_inputs`. The **new** hub tiles use `operator_entries`.

---

## 2. Table `operator_entries` – columns

| # | Column | Filled how? | Meaning |
|---|--------|-------------|---------|
| 1 | `id` | Auto | Unique entry ID |
| 2 | `company_id` | Auto (from run) | Company |
| 3 | `category` | Form | Form type (e.g. `dosing_material`) |
| 4 | `production_run_id` | Form | Linked production run |
| 5 | `event_time` | Form | When the event happened |
| 6 | `title` | Derived | Short title (e.g. from “What to record?”) |
| 7 | `status` | Derived | e.g. open / resolved / released |
| 8 | `operator_id` | Auto (logged-in user) | Who created it |
| 9 | `updated_by_id` | Auto | Who last changed it |
| 10 | `batch_label` | Form (summary) | Batch text for lists |
| 11 | `material_label` | Form (summary) | Material name for lists |
| 12 | `recipe_label` | Form / run | Recipe text for lists |
| 13 | `machine_label` | Form (summary) | Machine text for lists |
| 14 | `comment` | Form | Operator comment |
| 15 | `payload` | Form | **All detailed answers (JSON)** |
| 16 | `created_at` | Auto | Created timestamp |
| 17 | `updated_at` | Auto | Updated timestamp |
| 18 | `is_deleted` | Soft delete | Hidden when deleted |

**Summary:**

- Table has **18 columns**
- Operator form typically **fills / drives ~11 of them** (category, run, time, title, status, batch/material/recipe/machine labels, comment, payload)
- The rest are **system-filled** (IDs, timestamps, user, soft-delete)

The important idea: **question count ≠ column count**.  
A dosing form may ask ~21 questions, but they are all stored mainly inside **`payload`**, while a few summary fields are copied to dedicated columns for Recent Entries.

---

## 3. Forms at a glance

| Form (UI) | Route | `category` value | Questions operator answers | Plant values (display only) |
|-----------|-------|------------------|----------------------------|-----------------------------|
| Dosierung / Material | `/forms/dosing-material` | `dosing_material` | **21** | — |
| Extruder | `/forms/extruder` | `extruder` | **24** | — |
| Siebwechsler | `/forms/screen-changer` | `screen_changer` | **17** | 3 (planned live) |
| Düse / Düsenplatte | `/forms/die` | `die` | **18** | — |
| Wasserbox | `/forms/water-box` | `water_box` | **17** | 7 (planned live) |
| Granulator / Messer | `/forms/granulator` | `granulator` | **17** | 7 (planned live) |
| Qualitätsdaten | `/forms/quality` | `quality` | **~25** (across cards) | — |
| Allgemeines Ereignis | `/forms/general-event` | `general_event` | **11** | — |
| Letzte Einträge | `/forms/recent-entries` | *(no create form)* | — | — |

“Plant values” (`Anlagenwerte`) are **read-only context** from the plant/WinCC (spec). They are **not** written as operator answers yet; they currently show placeholders until live signals are connected.

---

## 4. What each form is for

### 4.1 Dosierung / Material (`dosing_material`) – 21 questions  
Records dosing deviations, raw-material issues, batch problems, material anomalies.  
Typical flow: **when** → **what happened** → **observations** → **measures** → **result** → **comment**.

### 4.2 Extruder (`extruder`) – 24 questions  
Records pressure/temperature/torque/speed issues, process instability, interventions and criticality/scrap impact.

### 4.3 Siebwechsler (`screen_changer`) – 17 questions  
Records screen inspection/change/cleaning, differential pressure, blockages and related measures.  
Includes planned display of differential / before / after pressure.

### 4.4 Düse / Düsenplatte (`die`) – 18 questions  
Records die / die-plate inspection, cleaning, change, outlet observations and wear-related findings.  
Quality lab results stay in the Quality form (clean separation: operator observation vs QA assessment).

### 4.5 Wasserbox (`water_box`) – 17 questions  
Records cooling problems (temperature, pressure, flow, leaks, alarms) and interventions.  
Includes planned display of process water values.

### 4.6 Granulator / Messer (`granulator`) – 17 questions  
Records knife change/grind/inspection, cut quality, dust, granulator faults.  
Includes planned WinCC display (speed, torque, knife position/pressure).

### 4.7 Qualitätsdaten (`quality`) – ~25 inputs in 9 cards  
Inspector/QA oriented: production info, inspection period, inspector, quality characteristics, link to production events, overall assessment, cause, comment, attachments (attachments UI still light).

### 4.8 Allgemeines Ereignis (`general_event`) – 11 questions  
For events that do **not** belong to one station (power, network, PLC/HMI, safety, etc.).

### 4.9 Letzte Einträge (Recent Entries)  
Not a capture form. Lists all `operator_entries`, with search/filter and detail panel (edit / export / duplicate / delete where allowed).

---

## 5. Shared question pattern (most station forms)

Most station forms follow the same logic from the specification:

1. Production run + event time  
2. Timeline (first occurred / noticed / resolved + durations)  
3. What should be recorded?  
4. What was observed?  
5. What effects / measures / other areas / suspected cause?  
6. Who was informed?  
7. Result  
8. Operator comment  

That consistency makes training and later AI use easier.

---

## 6. Status values (derived)

When saving, the app derives a **status** for lists/filters, for example:

| Status | Typical meaning |
|--------|-----------------|
| `open` | Still open / ongoing / partial |
| `resolved` | Problem fully resolved |
| `released` | Quality release |
| `hold` | Quality hold |
| `scrap` | Scrap assessment |

Exact mapping comes from the form’s “Result” / “Overall assessment” answers.

---

## 7. API (for developers)

| Method | Endpoint | Use |
|--------|----------|-----|
| `GET` | `/operator-entries` | List / filter (Recent Entries) |
| `GET` | `/operator-entries/{id}` | One entry |
| `POST` | `/operator-entries` | Create from a form |
| `PUT` | `/operator-entries/{id}` | Update |
| `POST` | `/operator-entries/{id}/duplicate` | Duplicate |
| `DELETE` | `/operator-entries/{id}` | Soft-delete (SuperAdmin) |

---

## 8. Quick mental model

```
Operator chooses tile
        ↓
Fills questionnaire (many questions)
        ↓
Saved as ONE row in operator_entries
        ↓
Summary columns  →  used by Recent Entries filters/list
payload JSON     →  full answers for detail / edit / AI later
```

---

*Document generated from the current Sanpor Predictive AI operator forms implementation.*
