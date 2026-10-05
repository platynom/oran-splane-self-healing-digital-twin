# AI-Native Self-Healing O-RAN Network Using a Digital Twin

This repository is currently in the architecture, literature-survey, and MVP-prototype phase.

The current MVP is a service-class-aware and AML-aware O-RAN Digital Twin simulator. It does not claim to be a production O-RAN deployment. It proves the closed-loop concept:

```text
Service profile -> simulated/OAI-style KPIs -> Digital Twin assessment
-> anomaly detection -> spectrum/resource monitor -> root cause analysis
-> healing recommendation -> adversarial ML guard -> policy validation
-> dashboard/evaluation/xApp-style outputs
```

The adversarial ML guard is based on the project literature review of AML threats in O-RAN. It treats the AI pipeline itself as a protected asset: telemetry, AI inference, RCA, and healing actions are checked before closed-loop automation is allowed.

## Service Classes

The MVP models five 5G service classes:

- `eMBB`: throughput-heavy broadband
- `mMTC`: massive IoT scale
- `URLLC`: ultra-reliable low-latency critical control
- `FWA`: fixed wireless access
- `V2X`: safety-critical mobility

Profiles live in:

```text
configs/service_profiles.json
```

## Current MVP Modules

| Module | File | Role |
|---|---|---|
| Service profiles | `oran_twin/profiles.py` | Loads target latency, jitter, throughput, reliability, priority, edge dependency, and service weights. |
| KPI simulator | `oran_twin/simulator.py` | Generates synthetic O-RAN KPI streams across cells and service classes. |
| Fault scenarios | `configs/fault_scenarios.json` | Defines injected cell congestion, spectrum interference, backhaul degradation, edge overload, handover instability, and timing drift. |
| Digital Twin | `oran_twin/digital_twin.py` | Compares live/simulated KPIs against service-class targets and computes risk. |
| Anomaly detector | `oran_twin/detector.py` | Rolling baseline anomaly detector for KPI deviations. |
| Spectrum monitor | `oran_twin/spectrum_monitor.py` | SpotLight-inspired radio/spectrum resource anomaly monitor with DSA policy output, spectrum band/channel selection, backup-band recommendation, channel occupancy, spectral efficiency, and interference-source classification. |
| Slice/SLA twin | `oran_twin/slice_impact.py` | E2E slice assurance twin with latency prediction, breach probability, affected-domain mapping, tenant impact, and what-if actions. |
| TSN/PTP timing twin | `oran_twin/timing_security.py` | STRIDE-based timing security twin with PTP domains, clock roles, offset estimation, sync state, attack surface, and remediation plan. |
| ZSM policy orchestrator | `oran_twin/policy_orchestrator.py` | CERBERUS-inspired secure automation layer with operator/tenant context, workflow stage, audit ID, escalation level, and MTTD/MTTM targets. |
| AI-enabled DTN orchestrator | `oran_twin/dtn_orchestrator.py` | Cross-domain readiness layer for DTN state, twin sync quality, AI service chain, orchestration mode, and capability gaps. |
| Automation safety scorer | `oran_twin/automation_safety.py` | Unifies AML, drift, xApp conflict, SLA, timing, spectrum, ZSM policy, and DTN evidence into one safety score with baseline-vs-guarded comparison. |
| Device population model | `oran_twin/device_population.py` | Represents lakhs of virtual 5G devices as service-level aggregates and representative UE samples. |
| Model registry | `oran_twin/model_registry.py` | Tracks active model metadata and rollback-ready versioning structure. |
| Local persistence | `oran_twin/persistence.py` | Stores local decisions and run summaries in SQLite for audit and reporting. |
| RCA | `oran_twin/rca.py` | Infers likely root cause from KPI signatures. |
| Healing engine | `oran_twin/healing.py` | Recommends recovery actions and validates them before approval. |
| AML security guard | `oran_twin/security_guard.py` | Scores AI trust, classifies adversarial ML threat level, and blocks unsafe automation. |
| Pipeline | `oran_twin/pipeline.py` | Runs the complete loop and writes CSV/JSON/HTML outputs. |
| Demo runner | `run_demo.py` | CLI entry point for a complete demo run. |

## Run the Demo

```powershell
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" run_demo.py --run-name demo_final_mvp --duration 240 --seed 42
```

Outputs are created under:

```text
outputs/runs/<run-name>/
```

Key files:

- `simulated_kpis.csv`
- `twin_assessments.csv`
- `summary.json`
- `evaluation_report.md`
- `incident_report.md`
- `dashboard.html`

Open `dashboard.html` in a browser to see the MVP dashboard.

## Current Expert Artifacts

For presentation or review, start with:

```text
PROJECT_INDEX.md
outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/00_OPEN_FIRST_README.txt
outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/01_FINAL_PRESENTATION.pptx
outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/08_PIPELINE_ROW_COUNT_RECONCILIATION.csv
docs/FINAL_EVIDENCE_REPORT.md
docs/PAPER_CITATION_INTEGRATION_MAP.md
```

Use the `SYNC_FIXED` expert pack for final review. It removes internal FlexRIC indication-latency parser noise from the normalized KPM/training path, so the main counts align as `71,900` corrected FlexRIC KPM/decision rows and `431,400` augmented training rows.

Historical milestone reports and older output snapshots are preserved under `_local_quarantine/` and should not be used for the final presentation.

## Demo Script

The concise demo script is available at:

```text
docs/DEMO_SCRIPT.md
```

Current best verified run:

```text
outputs/runs/local_hardening_full
```

Key metrics:

- precision: `0.8026`
- recall: `0.9048`
- F1-score: `0.8506`
- false positive rate: `0.0582`
- RCA accuracy on actionable faults: `0.9568`
- virtual devices represented: `1,867,043`
- active virtual devices represented: `200,453`
- estimated affected devices: `47,990`
- baseline executable actions: `875`
- guarded executable actions: `513`
- unsafe baseline actions prevented: `362`
- unsafe prevention rate vs baseline: `0.4137`
- mean automation safety score: `0.4192`
- injected AML attack guard rate: `1.0`
- predicted SLA breach records: `1132`
- severe SLA impact records: `477`
- timing security incidents: `111`
- SOC/NOC joint incidents: `230`
- autonomous-ready DTN records: `713`
- security-hold DTN records: `230`
- spectrum anomaly records: `31`
- spectrum watch records: `37`
- dynamic spectrum reassignment actions: `31`
- DSA policies: `switch_to_backup_band_n41_2p5ghz`, `switch_to_backup_band_n78_3p5ghz`, `probe_backup_channel_and_raise_sampling`

## Paper Integration Map

The consolidated mapping from papers/standards to implemented modules is available at:

```text
docs/PAPER_CITATION_INTEGRATION_MAP.md
```

The implementation now includes:

- RIC/xApp-ready runtime
- E2-style anomaly/fault signatures
- xApp conflict arbitration
- drift monitoring
- adversarial ML guard
- timing/PTP security twin
- spectrum/resource anomaly monitor
- dynamic spectrum access policy output
- unified automation safety score
- baseline-vs-guarded automation comparison
- large-scale virtual device population representation
- representative UE sample view
- local SQLite audit persistence
- local health check and logging
- slice/SLA impact twin
- AI-enabled DTN readiness orchestration
- ZSM/SMO-style policy orchestration

## Run the Live Interactive BLR Map GUI

The current product-style GUI is a localhost web app backed by a live Python API loop:

```powershell
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" live_backend.py --port 8080
```

Then open:

```text
http://127.0.0.1:8080/
```

Health check:

```text
http://127.0.0.1:8080/api/health
```

If port `8080` is busy, the server automatically prints the fallback URL, usually:

```text
http://127.0.0.1:8081/
```

The GUI lets you change:

- service class
- target Bengaluru cell
- fault type
- fault severity
- network load
- mobility pressure
- weather impact
- healing mode

## Run RIC/xApp-Style Mode

The same core decision engine can run without the GUI as a Near-RT RIC/xApp-style backend service:

```powershell
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" xapp_runner.py --input data\telemetry\sample_oai_like_kpis.csv --output outputs\xapp_decisions.jsonl --service eMBB
```

This mode reads normalized KPI rows and emits JSONL decisions shaped like xApp outputs:

```text
telemetry row -> shared decision engine -> RCA/healing/security/drift -> RIC control payload
```

Dual-runtime design:

| Runtime | Entry point | Purpose |
|---|---|---|
| Localhost GUI | `live_backend.py` | Demo, dashboard, scenario control, visual validation. |
| Batch evaluation | `run_demo.py` | Offline CSV/JSON/HTML experiment output. |
| RIC/xApp-style | `xapp_runner.py` | Headless decision service for normalized E2SM-KPM/OAI-like telemetry. |

Shared logic:

```text
oran_twin/engine.py
```

The localhost and xApp-style modes both use the same core decision engine. Only the runtime adapters differ.

It polls `/api/state` once per second and updates:

- BLR map cell risk
- predicted KPIs
- SLA status
- likely root cause
- healing recommendation
- AI trust score
- AML threat level and threat type
- security guard action
- twin validation result
- before/after risk

Current data model:

- Service targets come from `configs/service_profiles.json`.
- Standards grounding is documented in `configs/profile_sources.md`.
- Bengaluru weather is fetched from Open-Meteo when the laptop has internet.
- Telecom counters are profile-driven synthetic KPIs until OAI/RIC/operator telemetry is connected.
- OAI/srsRAN/E2 KPM counter mapping is defined in `configs/oai_counter_mapping.json`.
- OAI/FlexRIC setup notes are tracked in `docs/OAI_FLEXRIC_OPTION2_SETUP.md`.

Telemetry modes:

- `profile_simulation`: live synthetic KPI stream driven by service profiles, BLR topology, weather, and fault controls.
- `csv_replay`: replays normalized KPI rows from a CSV file.
- `oai_log_ingestion`: reserved for converted OpenAirInterface/srsRAN metric logs using the same KPI schema.
- `near_rt_ric_kpm`: reserved for normalized O-RAN E2SM-KPM measurements.

Sample replay data:

```text
data/telemetry/sample_oai_like_kpis.csv
```

Normalize raw lab telemetry:

```powershell
.\scripts\normalize_sample_telemetry.ps1
```

Or run the normalizer directly:

```powershell
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\normalize_telemetry.py --input data\telemetry\raw\sample_oai_metrics.log --output data\telemetry\normalized_oai_metrics.csv --cell-id CELL_A
```

Then in the GUI choose:

```text
Telemetry mode: OAI log ingestion
Source file: data/telemetry/normalized_oai_metrics.csv
```

Live file-watch replay:

1. Start the GUI.
2. Set telemetry mode to `OAI log ingestion`.
3. Set source file to:

```text
data/telemetry/live_oai_feed.csv
```

4. In another terminal run:

```powershell
.\scripts\start_live_feed.ps1
```

The backend watches the CSV timestamp and reloads new KPI rows automatically.

Live OAI-style collector:

```powershell
.\scripts\start_oai_collector.ps1
```

Bridge OAI/srsRAN runtime logs into collector input:

```powershell
.\scripts\start_oai_metric_bridge.ps1
```

Run the sample bridge once:

```powershell
.\scripts\bridge_sample_oai_runtime.ps1
```

Append a test raw OAI metric line:

```powershell
.\scripts\append_sample_oai_raw.ps1
```

Setup notes for the real OAI/FlexRIC lab path are in:

```text
docs/OAI_FLEXRIC_OPTION2_SETUP.md
```

### VS Code Tasks

Open the project folder in VS Code, then use:

```text
Terminal -> Run Task -> Start BLR Map GUI
```

Then open:

```text
http://127.0.0.1:8080/
```

Other tasks:

```text
Run MVP Simulation
Stop Port 8080 Server
```

You can also run the PowerShell scripts directly:

```powershell
.\scripts\start_gui.ps1
.\scripts\run_simulation.ps1
.\scripts\stop_gui.ps1
```

Validate the local prototype:

```powershell
.\scripts\validate_local.ps1 -RunName local_hardening_check -Duration 60 -Seed 42
```

If Docker Desktop is installed:

```powershell
docker compose up --build
```

## Current Fault Types

The MVP injects:

- cell congestion
- backhaul degradation
- edge/MEC overload
- handover instability
- timing drift

These map well to O-RAN self-healing literature and can later be expanded to xApp conflict, RU failure, fronthaul packet loss, PTP/SyncE instability, and 5G Core/UPF overload.

## Current Healing Actions

The healing engine recommends:

- `load_balance_neighbor_cell`
- `prioritize_slice_and_traffic_steer`
- `reroute_transport_path`
- `mec_failover_or_scale`
- `handover_parameter_tuning`
- `switch_timing_source`
- `resource_reallocation`
- `human_review_guarded_mode`
- `dynamic_spectrum_reassignment`

The Digital Twin validates actions before marking them approved.

## Adversarial ML Guard

The AML guard adds the security contribution from the adversarial machine learning O-RAN paper into the system. It checks whether the AI decision path is trustworthy before a healing action is approved.

Current checks include:

- injected AML attack scenarios for telemetry poisoning, model evasion, and unsafe xApp-control contexts
- impossible or inconsistent KPI ranges
- high anomaly score with low twin risk, suggesting model evasion or a blind spot
- high twin risk with quiet anomaly detector, suggesting poisoning or drift
- RCA/action mismatch, such as congestion recovery without PRB or loss evidence
- critical-slice control actions that should require stronger trust
- low-confidence AI decisions attempting automation

Outputs added to CSV, JSON, HTML dashboard, and live GUI:

- `ai_trust_score`
- `aml_threat_level`
- `aml_threat_type`
- `security_guard_action`
- `security_guard_reasons`
- `aml_attack_active`
- `aml_attack_type`

This turns the project into a secure closed-loop O-RAN prototype: the network can self-heal, but the AI and telemetry are also evaluated before automation is allowed.

## Drift Monitor / Model Lifecycle Layer

The second-layer model lifecycle module is implemented in:

```text
oran_twin/drift_monitor.py
```

It is based on the Open RAN drift-handling literature and monitors whether KPI distributions are moving away from the learned baseline. The current implementation is a lightweight window-based detector suitable for the MVP.

Outputs added to batch and live flows:

- `drift_score`
- `drift_status`
- `drift_type`
- `drift_adaptation_action`
- `drift_model_profile_id`
- `drift_lifecycle_stage`
- `drift_retraining_priority`
- `drift_automation_mode`
- `drift_reasons`

Supported lifecycle states:

- `warming_up`
- `stable`
- `warning`
- `drifted`

Supported drift types:

- `sudden`
- `gradual`
- `recurring`
- `incremental`

Supported adaptation actions:

- `collect_more_samples`
- `keep_model`
- `schedule_retraining`
- `prepare_known_model_profile`
- `freeze_automation_and_retrain`
- `switch_or_retrain_model`
- `reuse_known_model_profile`

If a drifted state is detected while a healing action is being considered, automation is blocked and the model lifecycle action is shown in the validation note.

The drift layer now also maps each drift state into a Non-RT RIC/SMO-style lifecycle plan: current model, retraining scheduled, candidate model required, model quarantine, known profile reuse, and the allowed automation mode.

## xApp Conflict Management Layer

The xApp conflict-management MVP is implemented in:

```text
oran_twin/conflict_manager.py
```

It is inspired by the xApp distillation and COMIX conflict-management literature. The current implementation does not train a DQN/neural student yet, but it now implements a practical teacher/student proxy:

- creates multiple teacher xApp-style proposals
- scores teachers using `configs/xapp_distillation_policy.json`
- buckets the current state by risk, slice criticality, radio stress, mobility stress, and capacity stress
- detects direct control conflicts
- detects indirect objective conflicts
- detects multi-xApp coordination risk
- selects one distilled student action before validation
- records an xApp replay item for later state-action-outcome training
- exposes the selected xApp and conflict type in GUI, CSV, HTML, and JSONL output

Current xApp-style teachers:

- `self_healing_xapp`
- `traffic_steering_xapp`
- `resource_allocation_xapp`
- `handover_optimization_xapp`
- `spectrum_monitor_xapp`
- `energy_saving_xapp`

Outputs:

- `xapp_conflict_detected`
- `xapp_conflict_type`
- `xapp_selected`
- `xapp_mitigation_strategy`
- `xapp_distillation_state`
- `xapp_replay_record`
- `xapp_proposals`
- `xapp_conflict_reasons`

This improves safe closed-loop control by preventing the system from blindly applying one action when multiple xApp-style objectives compete.

## Design Position

This MVP is intentionally the first build layer. The larger research vision remains:

```text
National-scale AI-native self-healing O-RAN Digital Twin platform
for telecom NOC assurance, fault prediction, RCA, adversarial-ML defense,
and safe closed-loop recovery.
```

Product angle:

```text
RIC/xApp/rApp safety validation layer that scores telemetry trust,
AI decision trust, and closed-loop recovery risk before O-RAN automation executes.
```

Next expansions:

1. Add trained ML classifiers and evaluation splits.
2. Add map-based road/cell visualization using OpenStreetMap/SUMO.
3. Add OpenAirInterface KPI integration.
4. Add near-RT RIC/xApp-style control loop.
5. Add adversarial scenario injection for telemetry poisoning, evasion, drift, and unsafe xApp actions.
6. Replace MVP xApp arbitration with learned policy distillation using state-action-outcome replay buffers.
7. Add report generation for literature matrix and experiment results.
