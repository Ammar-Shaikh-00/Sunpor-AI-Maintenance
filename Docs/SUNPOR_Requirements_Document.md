# SUNPOR × SCLERA — Project Requirements Document
**Project:** AI-based Process Monitoring, Early-Warning & Predictive Quality System for EPS Foam Extrusion
**Production line:** E10 (first line; system designed to extend to further lines later)
**Prepared by:** SCLERA Group — AI Solutions
**Client:** SUNPOR
**Document type:** Living requirements & development-path document (client-driven)
**Version:** 2.0
**Status:** Baseline for development

# 0. How to read this document
This document is the **single source of truth** for what we build and why. It is derived **from the client's stated needs** (meeting emails and the technical questionnaire).
Two important framing points:
1. **The client is a domain expert, not a technical/AI expert.** They tell us what they want the system to do; **we design, decide, and drive the technical realization** ourselves.
1. **There is no historical dataset available from the client.** All learning data — signal history, operator inputs, quality outcomes, maintenance events — will be **collected live** by our system from day one and built up over time.
The system is organized into **detection capabilities** (not numbered models). Each capability is described the same way:
- **Client need** — what SUNPOR wants, in intent
- **What it detects** — the concrete output the system produces
- **Inputs** — signals + operator forms + quality/maintenance data
- **How we develop it** — the method / approach, in stages if applicable
- **Dependencies** — what must exist first, either technically or in terms of collected data
- **Open items** — what we still need from the client to finish or improve it
All capabilities are treated as **equally important pillars**. Build order is driven by **technical dependency**, not by ranking one capability above another.

# 1. Client vision
SUNPOR does **not** want just a dashboard or a visualization of sensor values. The client wants an **intelligent assistance and interpretation system** for production that:
1. Analyzes process behavior across all plant areas.
1. Recognizes patterns in the collected production data and links them to quality outcomes over time.
1. Detects **early indicators** before a fault, stoppage, or quality loss occurs.
1. Predicts maintenance needs (tool wear: knives, screen, nozzle).
1. Prioritizes critical developments and actively supports operators.
1. Generates relevant warnings automatically (including mobile alerts).
Core principle stated by the client:
> "Not to react only after a fault has already occurred, but to make developments and anomalies visible as early as possible."

# 2. Central problems the system must solve

## 2.1 Delayed fault detection (early doser drift)
Changes appear **early at the dosing units** — longer feed-in/conveying times, abnormal vibration, dosing deviations — **before** the extruder or production reports a fault. Today these early signs are missed.
**Requirement:** Detect behavioral changes and early indicators **at the source**, ahead of the actual fault. This is a Phase-1 priority.

## 2.2 Delayed quality assessment
Final quality is measured **days after production** (product must foam, cure, and be stored). Quality problems are therefore only visible with a long delay.
**Requirement:** As soon as later quality results are recorded by the quality department, **correlate them back** to the run's captured signal and operator data, so the system progressively learns to **predict quality during production**.

## 2.3 Undocumented maintenance & operator events
Events such as knife change/sharpening, cleaning, material change, and manual interventions are often **not captured** in SCADA/production data, yet are essential for analysis.
**Requirement:** Capture these via operator input forms and use them as labels/context.

# 3. System scope

## 3.1 In scope
- Ingestion of live WinCC signals (Line E10, 104 tags today; more to be added).
- Data cleaning, quality tagging, and rolling history.
- Feature engineering over multiple time windows.
- Detection capabilities (Section 7) + correlation/learning layer.
- Operator input forms (events, material behavior, quality, blocking).
- Progressive live data collection to build the internal learning dataset.
- Correlation of production data with delayed quality results (as they arrive).
- Predictions/warnings stored and shown on dashboard; mobile/notification alerts.

## 3.2 Out of scope (explicitly)
- Recipes and confidential production parameters (client confirmed not required).
- Direct machine control / closed-loop actuation — the system is **advisory**.
- Replacing operator judgment — the system **assists**, operators decide.
- Reliance on any pre-existing historical dataset from the client (none is available).

## 3.3 Non-functional requirements
- **Advisory only:** no write-back to machine control.
- **Configurable at any time:** dropdown fields are data-driven and editable without redeployment; detection thresholds live in configuration and can be adjusted as experience grows (this directly answers the client's question about later dropdown/threshold changes).
- **Extendable:** adding a signal to a machine-area group automatically routes it to the right capabilities — no hardcoded tag names.
- **Robust:** ingestion / feature / prediction loops must never crash the service.
- **Traceable:** every prediction stores its input time window and a human-readable explanation.
- **Multi-line ready:** design must generalize from E10 to other lines.
- **Learns over time:** capabilities work in a basic (rule/heuristic) form from day one and improve automatically as live data accumulates.

# 4. Data sources

## 4.1 Automatic (WinCC signals — 104 tags on E10 today)
Grouped by machine area; groups are the unit of feature engineering.

| Signal group | Count | Primary use |
|---|---|---|
| heating_zones | 27 | Process State, Anomaly |
| feeders | 31 | Process State, Early Anomaly, Material Behavior |
| extruder_meltpump | 4 | Process State, Anomaly |
| melt_pressure | 5 | Process State, Nozzle/Screen, Predictive Quality |
| screen_changer | 14 | Nozzle/Screen, Anomaly |
| process_water | 7 | Material Behavior, Granulator, Anomaly |
| granulator | 6 | Granulator/Knife, Anomaly |
| pentane_nitrogen | 3 | Material Behavior, Anomaly |
| offspec | 5 | Predictive Quality, Anomaly |
| status | 1 | Process State |

**Signals to be added (client mentioned, not yet in export):** doser vibration sensors, doser feed-in/conveying times, doser filled/active status, granulator vibration, feeder 6/7 actual throughput. These are important for early doser fault detection (Section 7.2).

## 4.2 Operator forms (manual context & labels)
Production start; extruder events; granulator events; cleaning; faults; material behavior; material blocking; daily quality. (See Section 9.)

## 4.3 Quality department
Later quality assessments, anomalies, approvals/rejections — the **ground truth** for predictive quality.

## 4.4 Internal learning dataset (built by us)
Because no historical dataset exists, we build our own by continuously recording:
- All ingested signals and their computed features.
- All predictions (with input windows and explanations).
- All operator form entries.
- All quality-department outcomes.
- All maintenance events.
This dataset is what enables Predictive Quality (7.4) and the Correlation & Learning Layer (Section 10) to improve over time.

# 5. System architecture

```
WinCC / Backend  ──►  Ingestion (periodic poll)
                        │
                        ▼
                    Data Cleaner  (validate, deduplicate, quality tag:
                                   GOOD / STALE / OUT_OF_RANGE / BAD / MISSING)
                        │
                        ▼
                Rolling Window Buffer  (recent history per signal)
                        │
                        ▼
                  Feature Engine  (windows: 1m / 5m / 15m / 30m / full-run
                                   → mean, std, trend, rate-of-change)
                        │
                        ▼
   ┌────────────────────┼───────────────────────────────────────┐
   ▼                    ▼                                       ▼
Process State     Early Anomaly Detection             Specific Risk Detections
(+ low-prod       (state-aware baselines,             (Material Behavior,
 cause/severity)   doser drift)                        Granulator/Knife,
   │                    │                              Nozzle/Screen, Predictive Quality)
   └────────────────────┴───────────────────┬─────────────────┘
                                            ▼
                              Predictions + Prioritized Warnings (stored)
                                            ▼
                              Dashboard + Notifications (incl. mobile)

        Correlation & Learning Layer  ◄── joins each run's signals/predictions with
                                          later quality + maintenance events
                                          (data grows over time from live capture)
```

# 6. What is already implemented
The following foundation is built and running. It is the base for every detection capability described in Section 7. Marking this section explicitly avoids confusion between "planned" and "already delivered".

## 6.1 Ingestion (DONE)
A periodic poller reads the latest snapshot of all Line E10 WinCC values from the backend. Polling interval is configurable; the current default is every 10 seconds. The poller is asynchronous, timeout-guarded, and never crashes the service if the backend is temporarily unreachable — it simply skips the tick and tries again. Each successful poll increments a counter that is exposed for health checks.

## 6.2 Data Cleaner (DONE)
Every value received from the backend passes through the cleaner before entering the buffer. The cleaner does three things:
1. **Validation:** checks that the value has a numeric type, is not null, and has a plausible timestamp.
1. **Deduplication:** if a value with the same timestamp for the same signal is already in the buffer, the new copy is dropped.
1. **Quality tagging:** every value is tagged with one of five states:
- GOOD — normal value inside expected bounds.
- STALE — the value has not changed for longer than the configured "stuck sensor" threshold (currently 30 identical samples in a row for non-exempt signals).
- OUT_OF_RANGE — value is outside the bounds defined for its (group, role) combination (e.g. a temperature outside 0–350 °C).
- BAD — flagged as bad by the source or fails a strict validity check.
- MISSING — expected in this snapshot but not present.
Bounds are looked up by **signal role and group** (actual, setpoint, control output, error code, mode, status), which means negative control-output values (a normal PID heater command) are not flagged as bad. Unknown role/group combinations are passed through as GOOD rather than falsely rejected. This design means adding a new signal never causes false alarms.
Downstream capabilities distinguish between "any bad quality" and "hard fault" (only OUT_OF_RANGE or BAD) so a stuck or missing sensor never triggers a false Fault phase.

## 6.3 Rolling Window Buffer (DONE)
An in-memory buffer keeps the recent history of every signal (up to ~8 hours). New values are appended, and the oldest are dropped once the buffer is full. The buffer is the source for all feature computations. Because it lives in memory, feature computation is instantaneous and never touches the database.

## 6.4 Feature Engine (DONE)
At every tick, the feature engine computes a **feature vector per capability** from the current buffer contents. For each signal it slices the tail of the buffer for five parallel windows:
- **1 minute** — very short, sensitive to spikes.
- **5 minutes** — the primary window for Process State; balances responsiveness and stability.
- **15 minutes** — captures slow trends.
- **30 minutes** — supports slow-wear detection (screen clogging, knife wear).
- **Full-run** — everything the buffer holds, for run-level context.
For each window it computes: **mean, standard deviation, linear trend (regression slope), rate of change, minimum, maximum, and last value**. Values are then aggregated per group (mean of means, mean of last values, mean of trends, mean of standard deviations, bad-quality ratio per group, hard-fault ratio per group) so that rule engines can reason at the level of a machine area, not individual tags.
A window is considered "ready" for a signal only if enough samples have been collected; a whole vector is "ready" only if the primary window is ready for enough signals. This prevents predictions being made on incomplete data during startup.

## 6.5 Supporting mechanics already in place
- **Signal-catalog-driven routing.** Signals belong to a group in the backend catalog; adding a signal to a group automatically routes it to every capability that consumes that group. No tag names are hardcoded anywhere.
- **Prediction storage with input-window traceability.** Every stored prediction records the exact time window of data it was based on and a plain-text explanation of the rule/heuristic that produced it. This makes every alert defensible when questioned by an operator.
- **First operator input forms exist in the SUNPOR AI application** — production start, extruder events, granulator events, cleaning, faults, material behavior, material blocking, daily quality. UI testing is ongoing.
- **Process State Detection is already running in an initial form.** The **Stable production** phase is calibrated against real Line E10 data. The remaining eight phases still need client-provided definitions and live-captured examples before they can be marked as calibrated (Section 7.1).
Everything from Section 7 onward is built **on top of** this foundation.

# 7. Detection capabilities (development path)
Build order is by technical dependency. **Process State is built first** because every other capability must know the production phase — a signal that is normal in one phase (e.g. low melt pressure during an empty run) is a serious problem in another (during stable production). Without Process State, every risk capability would produce constant false alarms during startup, cleaning, and empty runs.
Each capability below is described in the same structure: client need, what it detects, inputs, how we develop it, dependencies, open items.

## 7.1 Process State Detection (foundation)
**Client need.** SUNPOR needs the system to know, at any given moment, **what the line is doing**. This is the single most important piece of context in the whole system: every warning, every quality risk, every maintenance hint depends on it. A pressure drop during an empty run is expected and should be silent; the same pressure drop during stable production is an alarm-worthy event. Without the phase context, every capability would produce false alarms.
**What it detects.** The current production phase, chosen from:
- **Heating up** — the line is coming up to temperature; extruder is not yet running or is very slow; heating zones are trending upward; feeders are idle; melt pressure is low; production status flag is 0.
- **Startup** — heating is complete; the extruder screw is ramping up; feeders are starting to dose; throughput is climbing toward setpoint; melt pressure is building.
- **Stable production** — the reference state for every quality/risk capability. Throughput is at setpoint, status flag is 1, pressures are within their normal band, heating variance is low, granulator is running.
- **Low production** — throughput is meaningfully below setpoint while the line is still in a producing state (not startup, not empty run). See sub-analysis below.
- **Cleaning run** — cleaning cycle in progress; typically the water system is on, feeders are off, and status is 0.
- **Empty run** — the extruder is running but no material is being fed; pressure is low, feeders idle, status is 0. This is a legitimate, planned state that must not trigger alarms.
- **Cooling down** — temperatures are trending downward; feeders and extruder are stopped.
- **Shutdown** — the line is at rest; temperatures are low, everything is near zero.
- **Fault** — the pattern indicates a real disturbance: hard-fault signal ratio is high or pressures show extreme variance not consistent with normal operation.
Each detection returns a phase name, a confidence value (fraction of the phase's rule conditions that were satisfied), whether the phase is a "calibrated" one (only Stable production today) or an "estimated" one, and a human-readable explanation.
**Inputs.** Total throughput actual and setpoint, extruder screw speed and torque, melt pressure and temperature, heating zone means and variances, melt pump speed and torque, feeder operating modes, material production status flag, and (from the feature engine) trend and standard-deviation values that describe how these are changing over the primary 5-minute window.
**How we develop it.** A configurable rule engine sits on top of the feature engine. Rules for each phase live in a YAML configuration file (rules_config.yaml). Each rule specifies a set of conditions on group-level features (e.g. feeders.mean_of_lasts >= 300, melt_pressure.mean_of_lasts >= 80, heating_zones.mean_of_stds < 5) with an operator (>=, <, ==, ...) and a threshold. A phase matches if a configurable fraction of its conditions pass (e.g. 70%). Phases have priorities so that in ambiguous situations the safer / more specific phase wins (fault always outranks everything, stable production outranks startup so real stable data is never misread as startup).
The workflow to calibrate the remaining phases is:
1. The client answers the phase definition questions (Section 13).
1. The system runs live and records candidate phases.
1. Operators confirm or correct the labeled phase in the dashboard.
1. The team adjusts the YAML thresholds so the rules match observed behavior.
1. The phase is marked as calibrated in the calibration status block.
**Dependencies.** Live ingestion and feature engine (both already implemented in Section 6).
**Open items (client).**
- The operator/floor definition of each phase (what signals tell an operator "this is startup" vs "this is stable production"?).
- The meaning of Material Production Status = 1 in each phase. Is the flag only 1 in stable production, or is it also 1 during startup, empty run, cleaning?
- The meaning of the feeder operating modes (GD, VR, VS, LF, EF, and any other codes actually used on E10). These modes are almost certainly the fastest way to distinguish phases at the feeder level.
- Date/time examples of each non-stable phase collected during live operation. Because there is no historical dataset, these examples will be collected in real time — the operator marks "we are now in [phase] because [reason]" and the system stores that as a labeled example.
### Sub-analysis — Low-Production Cause & Severity
**What it adds.** When Process State says "low production", this sub-analysis produces the extra detail: how far below setpoint the line is (severity), how long it has been low (duration), and the most likely cause among:
- Startup or shutdown transition (the phase engine hasn't flipped yet).
- Feeder fault (one or more feeders showing warning or scrap alarm).
- Material problem (a Material Behavior event was logged just before or during).
- Pressure or process instability (extruder/melt-pump torque or pressure variance is high).
- Screen or nozzle restriction (differential pressure across the screen is rising).
- Planned slowdown (an operator entered a Low Production event marked as "planned").
- Recipe or material change (Production Start or a Material change event was logged during).
**Inputs.** Total throughput actual vs setpoint, per-feeder actual vs setpoint, feeder operating modes, feeder error codes, and the new operator "Low Production" event with its cause dropdown and planned/unplanned flag.
**How we develop it.** Because Process State already detects the phase, this is a lightweight rule/heuristic on top of the Process State output — it is deliberately **not** a separate ML model. Planned slowdowns (operator-entered) are separated from real problems so they never generate a "problem" alert. Severity is computed as 1 - actual/setpoint clamped to [0, 1]; duration is a simple running counter of consecutive ticks where phase = low production.
**Open items (client).**
- What % below setpoint and for how long counts as "low production"? Does a 5-minute dip count, or only a sustained 15-minute drop?
- Should the comparison be against **total** throughput setpoint or per-feeder actual vs setpoint (or both)?
- How do operators currently record planned slowdowns? Should the low-production form default to "planned" when the shift supervisor initiates it?
- How does a **dosing scrap alarm** (EPS / pentane / nitrogen critical dosing) relate to low production? Is it classified as low production, as fault, or as its own category?

## 7.2 Early Anomaly Detection (Phase-1 priority)
**Client need.** This is the single **most-emphasized** pain point in every conversation with the client. The dosing units start behaving abnormally minutes before the extruder shows the effect, and today those early signs are missed. The system must catch abnormal doser behavior at the source — even where no explicit rule exists — so operators can react before an actual fault or scrap event.
**What it detects.** Per-group anomaly scores plus specific early-drift flags such as:
- Doser feed-in / conveying time creeping up over a shift.
- Abnormal vibration pattern on a specific doser.
- Unstable dosing (setpoint vs actual mismatch growing, or the setpoint-actual delta becoming more variable than usual).
- Extruder torque drifting up relative to its baseline for the current phase.
- Melt pressure standard deviation increasing beyond the phase norm.
- Any signal group deviating meaningfully from the baseline of "how this group behaves during stable production on this line".
Each flag comes with a score, a group, an "early warning" label, and a plain-text explanation of what changed.
**Inputs.** All signal-group window features. The 15-minute and 30-minute windows are the primary inputs (they see the slow drift; the 1-minute window catches sudden spikes). Priority signals when available: doser vibration, feed-in / conveying times, dosing deviations (all listed in Section 4.1 as "to be added").
**How we develop it.** In two stages:
1. **Statistical baselines per phase.** For each signal group and each phase, we compute a rolling baseline (a robust mean and dispersion) from live Stable-production data. Then any group whose current values fall too far from that baseline (measured by a robust z-score, or an isolation-forest-style multivariate score for groups with many signals) triggers an anomaly. Baselines are **phase-specific**: what is normal during startup is not normal during stable production and vice versa. This is why Process State (7.1) is a hard dependency.
1. **Signal-specific drift detectors** for the client's priority signals (feed-in time, vibration). These use short-vs-long-window comparisons to flag creeping changes long before any threshold alarm.
The baseline improves the longer the system runs. On day one, with sparse baseline data, only clear anomalies fire; as more stable-production hours accumulate, the baseline sharpens and subtler drift is caught.
**Dependencies.** Process State (for phase-aware baselines); the additional doser signals for full value (without them we can already flag anomalies on the existing signals, but the "early warning" quality is much stronger with vibration and timing data).
**Open items (client).**
- Availability and integration path for the doser vibration and feed-in / conveying-time signals.
- Which dosers, in the client's experience, most commonly develop these early drifts? (Ranking them helps us tune the alerting priority.)

## 7.3 Material Behavior Risk
**Client need.** Predict developing **material** problems early — the kind of problems that come from dosing or material composition rather than mechanical wear. These are the problems the operator notices on the floor as "the material is behaving strangely today": lumps, twin beads, foaming problems, sieve tolerance drift.
**What it detects.** Risk per problem type:
- **Lump formation** — visible clumps in the product.
- **Twin beads** — beads stuck together in pairs.
- **Material outside sieve tolerance** — grain distribution drifts out of spec.
- **Too little pentane** — insufficient foaming agent.
- **Too much pentane** — excessive pentane, affects density.
- **Poor foaming behavior** — beads do not foam properly during later processing.
Each risk is a score with an associated cause hypothesis (which signals or feeder deviations triggered it) and a plain-text explanation.
**Inputs.** Temperature and pressure profiles (mean, std, trend across heating zones and melt pressures), throughput, feeder proportions (EPS / graphite / recycled / off-spec), pentane and nitrogen flows, process water temperature and flow (linked to lump formation and twin beads per the questionnaire), granulator behavior, current material type from Production Start, current phase from Process State. Operator entries from the **Material Behavior form** provide labels (which problem was observed) and severity (1–5).
**How we develop it.** In stages:
1. **Day-one rule/heuristic checks** derived directly from the client's questionnaire answers. For example: pentane actual deviation relative to expected ratio → foaming risk; process water temperature approaching the 65 °C danger threshold → lump / twin-bead risk; graphite proportion causing torque fluctuation → extruder-linked material risk. These rules use client domain knowledge as their starting point, so the system produces useful output from the first day, even without any collected data.
1. **Progressive learning from operator labels.** As operators log material-behavior events during stable production, the correlation layer joins those events with the signal patterns of the preceding minutes. Over time the system learns the specific patterns that precede each problem type on Line E10 (not on generic EPS lines) and refines the rules or moves to an ML classifier.
**Dependencies.** Process State (only makes sense during stable production); operator behavior logging (labels for learning); the client's cause knowledge (Section 13).
**Open items (client).**
- The causes per problem — the questionnaire answers cover most of this, but we need confirmation of the ranked "most likely causes" per problem for Line E10 specifically.
- Which dosers are critical (EPS / pentane / nitrogen → scrap) versus warning-only (graphite / 600 / off-spec / recycled → warning).
- Historical experience: material mixtures that have caused customer complaints in the past (approximate, not recipe).

## 7.4 Predictive Quality
**Client need.** This is the most ambitious capability: predict later (lab) quality **during** production, days before the lab result arrives. It solves problem 2.2 (delayed quality assessment) directly. If the system can flag a run as "high risk for open holes" or "high risk for foaming NOK" while the run is still in progress, operators can intervene, adjust, or stop the run — saving material that would otherwise become scrap and be caught only after packaging.
**What it detects.** Quality risk **per run** for:
- **Open holes** — percentage risk that the daily quality measurement will be poor.
- **Sieve distribution** — risk that the sieve analysis will fall outside tolerance.
- **Foaming OK/NOK** — risk that foaming will be classified as Not OK.
- **Cell structure problems** — risk of poor cell structure (raw material moisture, nitrogen dosing, per the questionnaire).
- **Material blocking risk** — probability the run will later be blocked retroactively.
Each risk is a percentage with a driver (which signals / events pushed the risk up) and an explanation.
**Inputs.** The full set of stable-phase signals — melt pressure, off-spec counters, granulator behavior, pentane / nitrogen, feeder behavior, process water, screen/nozzle temperatures — plus any maintenance events logged during the run, plus any Material Behavior events. The **targets** (what the system is being trained to predict) come from live capture going forward: **Daily Quality forms**, **Material Blocking forms**, and **Quality-department assessments** as they arrive after the run.
**How we develop it.** In two stages:
1. **Rule-based risk scores from day one.** Even before any ML training, we can produce a useful risk score by summing evidence: if pentane is deviating from its normal ratio, foaming risk rises; if off-spec coarse/fine counters are rising fast during stable production, sieve risk rises; if die-plate temperatures are unstable, open-holes risk rises; if the run had a Material Behavior event logged, all risks associated with that event rise. This gives the operator a live risk picture from day one.
1. **ML-based prediction** kicks in once the Correlation & Learning Layer (Section 10) has accumulated enough runs with outcomes. For each run we have a labeled example: (signal statistics + events during the run) → (later quality outcome). Standard supervised learning (gradient-boosted trees / logistic regression as baselines; more complex models as data grows) then produces a probability per quality outcome. The system compares the current run against historical **"good" runs** on the same material type and flags deviations.
Because the client has no historical dataset, ML predictions will start out only for the quality outcomes we get many labeled examples of first (probably daily quality — one entry per shift). Slower-to-arrive outcomes (material blocking) take longer to accumulate but eventually feed the same layer.
**Dependencies.** Process State (only stable production is used for training), Material Behavior (its predictions and operator labels are inputs), Nozzle/Screen and Granulator (their risks contribute), the Correlation & Learning Layer, and enough live-collected runs with outcomes.
**Open items (client).**
- How, when, and by whom are open holes, sieve, and foaming measured? What are the "OK" thresholds — is there a numeric cutoff for open-holes %, or is it a judgment?
- How soon after production is a run typically blocked, and who initiates the block?
- Raw-material moisture is mentioned as a cause of cell-structure problems in the questionnaire. Is it recorded anywhere today, or should we add it as an operator field on Production Start?

## 7.5 Granulator / Knife Wear
**Client need.** Predict when a knife needs to be changed or sharpened, and detect grain-distribution problems before they show up as scrap. Today the client decides on knife maintenance based on cut pattern (visual) and twin beads in sieve analysis. The system should get ahead of this.
**What it detects.**
- **Knife condition** — normal or approaching maintenance, with an estimated "remaining life" hint.
- **Grain distribution risk** — probability that the current run will drift out of sieve tolerance.
- **Maintenance recommendation** — a specific hint like "schedule knife sharpening within next 4 hours" or "knife change recommended before next material change".
**Inputs.** Granulator speed setpoint/actual, granulator torque, knife position, hydraulic contact force setpoint/actual, process water (cooling affects cutting quality), off-spec coarse and fine counters. Once available: granulator vibration. From forms: knife change and knife sharpening events; twin-bead observations; sieve % from daily quality.
**How we develop it.** Track torque and contact-force trends between logged knife events. When a knife change happens, the "clock" resets — the signal statistics right before the change become one training example of "a knife needing maintenance", and the statistics right after become one example of "a fresh knife". Over many knife events, the system learns the drift pattern that precedes the change. Off-spec drift (rising sieve coarse or fine counters) reinforces the signal. Sieve % from the daily quality form gives us the outcome to correlate with.
Because knife events are relatively rare (compared to signals), this capability takes longer to become highly accurate — but it starts producing useful trend-based hints from day one.
**Dependencies.** Process State (only judge knife health during stable production); knife-event logging going forward.
**Open items (client).**
- What is the earliest specific indicator that a knife needs to be changed or sharpened, in the operator's experience? (The questionnaire says "no typical signal change" — but we need to verify this against real data.)
- Typical time from "cut pattern getting worse" to "knife change performed"?

## 7.6 Nozzle / Screen / Pressure
**Client need.** Detect nozzle blockage, screen clogging, and pressure problems early, before they force an intervention or affect quality. The primary indicator today is differential pressure across the screen changer; the client answers in the questionnaire also point to inlet/outlet pressure trends and die-plate temperature evenness.
**What it detects.** A pressure-problem risk yes/no plus a probable cause:
- **Screen clogging** — inlet minus outlet melt pressure across the screen changer is rising.
- **Nozzle blockage** — startup valve pressure rising, die-plate temperatures becoming uneven.
- **Blockage elsewhere** — melt pump torque high, extruder torque high, generic pressure imbalance.
**Inputs.** Melt pressures 1–4, screen changer inlet and outlet melt pressures, startup valve pressure, die-plate temperatures (looking at evenness across all die zones), melt temperature, extruder torque, melt-pump torque. From forms: screen change events, nozzle change / flushing / grinding events, open holes % (daily quality), nozzle-blockage faults.
**How we develop it.** Rule-based from day one using the questionnaire answers:
- Differential pressure (inlet − outlet) trend rising → screen clogging risk (calibrated against the client's ΔP thresholds once provided).
- Die-plate temperature standard deviation across zones rising → nozzle unevenness risk, correlated with open-holes % from daily quality.
- Startup valve pressure rising → nozzle blockage risk.
As screen/nozzle events accumulate in operator forms, the system learns the specific ΔP levels and trend rates on Line E10 that actually preceded a required change, and refines its rules.
**Dependencies.** Process State (screen ΔP behaves differently in startup vs stable run); screen/nozzle event logging going forward.
**Open items (client).**
- Differential-pressure thresholds for "change soon" vs "change now" in bar.
- Symptoms operators watch for before nozzle change / grinding (the questionnaire mentions "inflatable boat" shapes, lumps, sieve deviations, open holes — we need to know which is most reliable as a signal).
- Which quality traits deteriorate first when the nozzle is starting to fail?

## 7.7 Maintenance Prediction & Prioritization
**Client need.** Turn the raw risk outputs from Granulator/Knife, Nozzle/Screen, and Early Anomaly into a **prioritized** list of hints for operators and shift leaders. In a shift many small issues happen at once; the client wants a single ranked view that answers "what should I look at first?".
**What it detects.** Maintenance risk (knife / nozzle / screen) with an urgency level, plus a ranked list of the current most-critical developments across the whole line. Each item includes the capability that produced it, the group affected, the urgency, a suggested action, and an ETA if relevant.
**Inputs.** Outputs of Granulator/Knife (7.5), Nozzle/Screen (7.6), and Early Anomaly (7.2), plus the live-captured maintenance-event history (to avoid repeatedly recommending an action that was just performed).
**How we develop it.** Aggregate individual risks into prioritized recommendations. Priority is a function of urgency, severity, and time-since-last-action for that specific maintenance type. Surface the prioritized list on the dashboard and drive notifications (in-app; mobile capable) for the top items.
**Dependencies.** Granulator/Knife, Nozzle/Screen, Early Anomaly.
**Open items (client).**
- Preferred alerting channels (email, mobile push, SMS, in-app only?) and escalation rules (who is alerted for what urgency).

# 8. Prediction outputs (stored and shown)
Every capability writes its output to the backend as an ml_prediction, with a consistent shape so the dashboard can display them uniformly. Rules stored on every prediction:
- Timestamp of prediction.
- Input window start and end (real data window, not compute time).
- Model name (e.g. process_state_rule_v1).
- Prediction type (from the table below).
- Prediction value (number or index).
- Confidence.
- Human-readable explanation.
- Link to the production run it belongs to.

| Output type | Source capability | Meaning |
|---|---|---|
| process_state | Process State | Current phase index + confidence |
| low_production_detail | Process State (sub-analysis) | Severity (fraction below setpoint), duration (ticks), cause label |
| anomaly_score | Early Anomaly | Score per group, plus early-drift flags |
| material_behavior_risk | Material Behavior | Risk score per problem type, with the driver signals |
| quality_risk | Predictive Quality | Predicted quality risk per run, per outcome type |
| granulator_risk | Granulator/Knife | Knife condition, grain risk, maintenance hint |
| pressure_problem_risk | Nozzle/Screen | Screen / nozzle / blockage risk with probable cause |
| maintenance_risk | Maintenance Prioritization | Ranked maintenance recommendations |

**Rule:** quality and maintenance warnings apply **only during stable production** — they are gated by Process State. During startup, empty run, cleaning, cooling, or shutdown, these outputs are suppressed on the dashboard (they still may be computed internally for learning purposes).

# 9. Operator forms — requirements
The operator forms are the human input side of the system. They are the primary source of **labels** for every learning capability, and they provide the **context** that makes signal data interpretable in real time. Because operators fill them under time pressure during a shift, the forms must be quick, use the language operators actually use, and have dropdowns rather than free text wherever possible.
All dropdown values are stored in the backend and are **editable at any time** without redeploying the application — this directly answers the client's question in the reply email.

| Form | Key fields | Feeds which capability |
|---|---|---|
| Production start | material type, trial (yes/no), shift, start time, comment | Context for every capability (all outputs are stamped with these) |
| Extruder events | Level 2 (phase or maintenance category), Level 3 (specific event), reason, time, comment | Process State (phase labels), Nozzle/Screen (screen and nozzle events) |
| Granulator events | Level 2 = Knife, Level 3 = Knife change / Knife sharpening, reason, time | Granulator/Knife |
| Cleaning | Level 2 (water bath / centrifuge / general cleaning work), reason, time | Process State (cleaning phase label) |
| Faults | Level 2 (mechanical / electrical), Level 3 (specific subtype), text field, time | Process State (fault phase), Nozzle/Screen (nozzle blockage faults) |
| Material behavior | behavior type dropdown (6 options from Section 4.2), severity 1–5, time, comment | Material Behavior (labels + severity) |
| Material blocking | reason dropdown (from Section 4.2), from-time, to-time, affected material, comment | Predictive Quality (ground truth for a bad batch) |
| Daily quality | shift, input time, open holes %, sieve distribution %, foaming behavior (OK / Not OK), comment | Predictive Quality (labels), Granulator (sieve %), Nozzle/Screen (open holes %) |
| Low production (new) | cause dropdown, planned / unplanned flag, start/end time, comment | Process State (sub-analysis) |

**Form requirements to implement:**
1. **Faults form:** Level 3 must switch dynamically based on Level 2. Today the form only shows mechanical Level 3 options — the electrical option (Power Failure) is not selectable when Level 2 = Electrical. This must be fixed.
1. **Extruder events form:** Level 2 → Level 3 must cascade to prevent invalid combinations (currently all Level 3 options are shown regardless of Level 2, so an operator can pick a nozzle sub-action under a heating Level 2, which is meaningless).
1. **Low Production entry:** add a new Level 2 = "Low Production" on the extruder events form with a cause dropdown (see the list in 7.1 sub-analysis) and a planned/unplanned flag.
1. **Daily quality:** confirm with the client whether the entry frequency is per-shift (implied by the shift field), and whether a shift can have multiple entries or one summary entry.
Operators are the **primary source of labels** for every learning capability, so these forms are not optional — they are a hard dependency for Material Behavior, Granulator/Knife, Nozzle/Screen, and Predictive Quality to become useful.

# 10. Correlation & Learning Layer
Because the project starts with **no historical dataset**, this layer is essential. It accumulates a labeled dataset entirely from live operation, and is what allows Predictive Quality and every "risk" capability to improve from rule-based to ML-based over time.
The layer works run by run. A **production run** is created when the operator submits Production Start; it is the context container for everything that happens until the run is stopped. During the run:
1. The system stores **all ingested signals** and their computed feature vectors, tagged with the run id.
1. The system stores **every prediction** from every capability, tagged with the run id and the input window.
1. Operators log **events (extruder, granulator, cleaning, faults), material behavior observations, and daily quality entries** through the forms; each is attached to the run id.
After the run ends (may be hours or a full shift):
1. **Material blocking entries** appear (typically days later when the quality department confirms a problem). Each block entry is joined back to the run(s) it affects, by material and time range.
1. **Quality-department assessments** (approvals, rejections, anomalies) are joined back to the corresponding run.
Now the run has a complete labeled record: its signal history, computed features, live predictions, operator events, and later outcomes. Over many runs this becomes the **training dataset**:
1. The system learns which signal patterns during production consistently preceded specific quality outcomes. This is the input for training the Predictive Quality ML model.
1. Current runs are continuously compared against accumulated "good runs" on the same material type. Anywhere the current run deviates meaningfully from historical good runs, a warning is raised — even without an explicit rule.
The longer the system operates, the stronger every capability becomes. This is by design: the client has no historical data, so the system's ability to learn from its own live operation is the only path to progressively better predictions.

# 11. Roles & responsibilities
The system is a partnership between three human roles and two automated roles. All roles are required — a gap in any one weakens the outputs.

| Role | Responsibility |
|---|---|
| Operators / production staff | Log maintenance actions (knife change/sharpening, screen change, nozzle work), tool changes, cleaning, material changes, manual interventions, material behavior observations on the floor, low-production causes, and daily quality (open holes %, sieve %, foaming OK/NOK). These logs are the primary labels for every learning capability. |
| Quality department / responsible staff | Record quality assessments, anomalies, approvals, rejections, and material blockings. This is the ground truth for Predictive Quality. |
| System (automatic capture) | Ingest and clean all WinCC signal values, tag their quality, buffer recent history, compute features across time windows, run all detection capabilities, store predictions with input windows and explanations, and generate warnings. |
| System (dashboard & notifications) | Display predictions and warnings with prioritization; deliver in-app and mobile notifications for critical events. |
| SCLERA (us) | Design the pipeline and capabilities; make every technical decision (algorithms, thresholds, architecture); calibrate rules using client answers and live-captured data; integrate operator forms; deliver the dashboard; run the Correlation & Learning Layer; evolve rule-based capabilities to ML as data accumulates; maintain and extend to further lines. |

# 12. Development roadmap (project completion path)
Ordered by dependency. Capabilities remain equally important in the final system; the order here reflects only what must be built first for the next thing to work.
**Phase 0 — Foundation — DONE**
- Ingestion (periodic poll from backend).
- Data cleaner with full quality tagging (GOOD / STALE / OUT_OF_RANGE / BAD / MISSING).
- Rolling window buffer in memory.
- Multi-window feature engine (1m / 5m / 15m / 30m / full-run).
- Signal-catalog-driven routing (adding a signal to a group auto-routes to the right capability).
- Prediction storage with input-window traceability and human-readable explanations.
- First operator forms in the SUNPOR AI application (UI testing ongoing).
- Initial Process State pipeline running; **Stable production** phase calibrated on live E10 data.
**Phase 1 — Process State + Early Doser Anomaly (client priorities)**
- Complete and calibrate all 9 phases (needs client definitions from Section 13 and live-captured phase examples marked by operators).
- Add the Low-Production Cause & Severity sub-analysis.
- Stand up Early Anomaly Detection with phase-aware baselines. Prioritize doser drift — add doser vibration and feed-in / conveying time signals as they become available.
- Show current phase and early warnings on the dashboard, with the explanation and input window shown.
**Phase 2 — Data foundation for quality**
- Fix the operator form gaps (fault Level 3 dynamic, extruder Level 2→3 cascade, add Low Production entry, confirm daily quality frequency).
- Ensure consistent operator + quality-department capture during every run.
- Build the Correlation & Learning Layer — the plumbing that joins run signals with later quality and maintenance events, and produces per-run labeled records.
**Phase 3 — Specific risk capabilities**
- Material Behavior — rule-based from client cause knowledge; improves as operators log behavior events.
- Granulator/Knife — trend-based from day one; improves as knife events accumulate.
- Nozzle/Screen — rule-based on ΔP and die-plate evenness; refines as screen/nozzle events accumulate.
**Phase 4 — Predictive Quality**
- Rule-based risk scores from day one (pentane deviation, off-spec drift, die-plate variance, material behavior events).
- Once enough runs with outcomes are collected live, train the ML model to predict quality risk during production; compare current runs to accumulated good runs on the same material type.
**Phase 5 — Maintenance prioritization + Notifications**
- Aggregate individual risks into a ranked recommendation list on the dashboard.
- Deliver in-app and mobile notifications for the highest-priority items, with escalation rules per client preference.
**Phase 6 — Hardening & multi-line**
- Ongoing rule/threshold recalibration as more live data accumulates.
- Extend from Line E10 to further lines (configuration-only, no code changes for signal routing).

# 13. Open items / client dependencies (consolidated)
Grouped by category. These are what unblocks or improves the roadmap phases above.
**Signals / data**
- Add doser vibration sensors to the WinCC export.
- Add doser feed-in / conveying times.
- Add doser filled / active status.
- Add granulator vibration.
- Add feeder 6 (pentane) and feeder 7 (nitrogen) actual throughput (currently only setpoint is present).
**Definitions & thresholds (needed for Process State + Low Production)**
- Meaning of Material Production Status = 1 in each production phase.
- Meaning of the feeder operating modes (GD, VR, VS, LF, EF, and any others).
- Operator/floor definition of each phase (what tells you it is startup vs stable vs empty run vs cleaning vs cooling vs shutdown vs fault).
- Phase examples during live operation — operators mark "we are now in [phase]" so the system can label real data.
- Low-production threshold (% below setpoint + duration) and how planned slowdown is recorded.
- Differential-pressure thresholds for screen ("change soon" vs "change now").
- Water-box normal ranges — largely provided in the questionnaire (58–61 °C water temp, alarm at 64 °C, foam at 65 °C, ~10.1 bar), to be confirmed live.
- Critical (scrap) vs warning dosers and their thresholds — partly provided.
**Quality**
- Measurement method, frequency, and thresholds for open holes %, sieve %, and foaming OK/NOK.
- Typical timing between run completion and material blocking (if a run is blocked).
- Whether raw-material moisture should be added as an operator field on Production Start (it is mentioned in the questionnaire as a cause for cell-structure problems).
**Process understanding (from the questionnaire — largely answered, needs confirmation for E10 specifics)**
- Cause–effect relationships per station (mostly answered).
- Typical faults per station (mostly answered).
- Operator interventions during ongoing operation (mostly answered).
- Daily decisions of shift supervisors and machine operators (mostly answered).
**Operations**
- Preferred alerting channels (in-app, email, SMS, mobile push).
- Escalation rules — who is alerted at which urgency level.

# 14. Success criteria
The project is considered successful when:
- **Process State** correctly labels all 9 phases on live Line E10, validated by operators on the floor. When the operator says "we are in startup", the system agrees.
- **Low-production events** are reported with the correct cause and severity, and the system does **not** produce false alarms during normal startup, shutdown, empty runs, or planned slowdowns.
- **Early doser anomalies** are flagged by the system **before** they are reported today by the existing threshold alarms. Every early anomaly the operator can confirm as a real problem is measured; the ratio of true early warnings to false alarms is tracked and improves over time.
- **Early warnings** are issued **before** the actual fault or quality loss for the main problem types (screen clogging, nozzle blockage, dosing drift, material-behavior symptoms).
- **Predictive Quality** flags risky runs **during** production, and those risks are later confirmed by lab / quality-department results at a measurable rate above chance. This starts small (rule-based) and improves as the internal dataset grows.
- **Maintenance hints** precede the actual knife / nozzle / screen intervention in a majority of cases, giving operators lead time.
- The **internal learning dataset** grows continuously from live operation; capability accuracy measurably improves as more labeled runs accumulate. This is the concrete way we show the system is "learning".
- The system remains **advisory, configurable, extendable, and multi-line ready** — no machine control, dropdowns editable at any time, thresholds editable in config, and new signals or new lines require configuration rather than code changes.

*This is a living document. Update definitions, thresholds, status of each capability, and open items as client answers arrive and as live data accumulates.*
