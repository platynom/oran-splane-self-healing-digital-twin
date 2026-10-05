# Project Index

## What To Open First

Start here if presenting the project to mentors, reviewers, or interviewers:

1. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/00_OPEN_FIRST_README.txt`
   Open this first. It gives the corrected order for the final PPT and synced CSV evidence.

2. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/01_FINAL_PRESENTATION.pptx`  
   Final corrected presentation. Use this copy with the synced CSV pack.

3. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/08_PIPELINE_ROW_COUNT_RECONCILIATION.csv`
   Explains why the project has 71,900 decision/KPM rows, 431,400 augmented training rows, and 6,250 benchmark test rows.

4. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/10_training_data_what_models_trained_on/00_OPEN_TRAINING_README.txt`
   Open this only when reviewers ask what the models were trained on. It sits inside the show-first folder and contains the corrected 431,400-row training CSV plus summary, distribution, sample, and column-guide CSVs.

5. `docs/FINAL_EVIDENCE_REPORT.md`  
   Final technical evidence, latest metrics, limitations, and monetizable positioning.

6. `README.md`  
   Main project overview, runnable commands, modules, and demo modes.

7. `docs/PAPER_CITATION_INTEGRATION_MAP.md`  
   Papers/standards used, why they matter, and exactly where they are integrated in the codebase.

8. `outputs/evidence/controlled_fault_evaluation.md`  
   Timestamped controlled fault-injection validation summary.

9. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/02_EXPERT_CSV_INDEX.csv`  
   Expert-facing CSV pack. Open this first if reviewers want spreadsheet-readable evidence instead of JSON.

10. `outputs/EXPERT_SHOW_FIRST_PACK_2026-06-17_SYNC_FIXED/01_show_first/07_FULL_FLEXRIC_DECISION_ROWS.csv`  
   Clean CSV export of the 30-minute FlexRIC KPM decision stream.

Do not present older PPTX files from `_local_quarantine/`. They are historical drafts or stale exports.

## Current Status

The project is a demo-ready and resume-ready AI-native O-RAN digital twin prototype.

It implements:

- O-RAN KPI simulation and normalized telemetry ingestion
- FlexRIC KPM evidence pipeline
- Open RAN KPM dataset training and benchmarking
- AI/ML-based anomaly detection and online self-learning
- RCA and healing recommendations
- xApp-style decision output
- AML, drift, timing, spectrum, SLA, and xApp conflict safety guards
- timestamped controlled fault-injection validation
- local dashboard and SQLite audit evidence

## Best One-Line Claim

```text
An AI-native self-healing O-RAN digital twin that ingests FlexRIC/Open RAN KPM telemetry, detects anomalies, performs RCA, recommends guarded healing actions, and exports auditable xApp-style decisions.
```

## What We Can Honestly Claim

- We used AI/ML models at prototype level.
- We used online self-learning, Isolation Forest, Random Forest, Gradient Boosting, and drift/anomaly scoring.
- We validated a 30-minute FlexRIC KPM run.
- We added controlled timestamped fault-injection labels for research-style evaluation.
- We generated CSV/JSON/Markdown evidence artifacts.
- We included O-CU, O-DU/High-PHY, O-RU/Low-PHY, core/transport, SMO, and xApp supporting benchmark/model evidence where it is useful for the architecture story.

## What We Should Not Overclaim

- This is not a production O-RAN deployment.
- This does not yet perform real E2 control actuation on a live operator RAN.
- This does not use deep learning neural networks yet.
- The controlled fault-injection test is lab/replay validation, not independent operator fault truth.

## Clean Folder Guide

| Folder | Purpose |
|---|---|
| `oran_twin/` | Core digital twin, AI/ML, RCA, healing, safety, policy, and xApp logic |
| `tools/` | Data import, normalization, live streaming, reports, controlled fault evaluation |
| `scripts/` | Repeatable PowerShell/Python workflow commands |
| `configs/` | Service profiles, fault scenarios, policy profiles, topology, model registry |
| `docs/` | Reports, evidence, architecture notes, literature implementation maps |
| `data/` | Small source/training/telemetry CSVs and summaries |
| `outputs/expert_csv/` | Preferred expert-facing spreadsheet evidence converted from current JSON outputs |
| `outputs/evidence/` | Decision-level CSVs and controlled fault-injection CSV/Markdown evidence |
| `outputs/reports/` | Current final 30-minute FlexRIC report source JSON/Markdown |
| `outputs/benchmarks/` | Current benchmark source JSONs; use `outputs/expert_csv/` for expert-facing CSV views |
| `outputs/presentations/` | Use `O-RAN_AI_Native_Self_Healing_Final_Expert_Review.pptx`; any locked older PPTX can be quarantined after PowerPoint closes |
| `web/` | Local dashboard frontend |
| `assets/` | Architecture images |
| `_local_quarantine/` | Historical runs, stale presentations, duplicate outputs, and confusing artifacts kept out of the main view |

## Current Evidence Set

| Artifact | Use |
|---|---|
| `outputs/presentations/O-RAN_AI_Native_Self_Healing_Final_Expert_Review.pptx` | Final presentation to show experts |
| `outputs/expert_csv/00_EXPERT_CSV_INDEX.csv` | CSV index for all expert-facing evidence tables |
| `outputs/expert_csv/flexric_30min_report_summary.csv` | Final 30-minute FlexRIC report in CSV form |
| `outputs/expert_csv/flexric_30min_balanced_benchmark_model_metrics.csv` | Current benchmark metrics in CSV form |
| `outputs/expert_csv/controlled_fault_summary.csv` | Controlled fault-injection accuracy metrics in CSV form |
| `outputs/expert_csv/controlled_fault_window_results.csv` | Per-window controlled fault results in CSV form |
| `outputs/evidence/flexric_kpm_30min_decisions.csv` | Clean 30-minute decision CSV |
| `data/training/flexric_kpm_30min_augmented_training_syncfixed.csv` | Final corrected training CSV |
| `outputs/expert_csv/model_inventory.csv` | CSV summary of current trained model artifacts |

## Best Demo Commands

Run local validation:

```powershell
.\scripts\validate_local.ps1 -RunName expert_check -Duration 30 -Seed 42
```

Controlled fault-injection results are already exported for experts as:

```text
outputs/expert_csv/controlled_fault_summary.csv
outputs/expert_csv/controlled_fault_window_results.csv
outputs/evidence/controlled_fault_decisions.csv
```

Regenerate the expert CSV pack after any new JSON-producing run:

```powershell
python tools\export_expert_csv_pack.py --output-dir outputs\expert_csv
```

Run stronger 2-hour KPM evidence when lab time is available:

```powershell
.\scripts\run_kpm_evidence_pipeline.ps1 -DurationSeconds 7200 -RunName flexric_kpm_2hr -SkipPatch
```
