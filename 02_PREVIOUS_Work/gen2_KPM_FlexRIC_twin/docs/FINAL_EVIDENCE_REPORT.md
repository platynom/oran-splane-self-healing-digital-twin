# Final Evidence Report

## Positioning

This project is best positioned as an AI-native RAN assurance and xApp validation sandbox. It is application-based and monetizable because it gives an operator, lab, or vendor team a local way to test self-healing policies before pushing automation into a RIC/SMO workflow.

The strongest claim is:

```text
A laptop-runnable O-RAN digital twin that ingests FlexRIC KPM telemetry, converts it into a common KPI schema, runs anomaly/RCA/healing decisions, applies safety gates, stores audit evidence, and generates replayable benchmark artifacts.
```

The project should not be described as a production O-RAN deployment yet.

## Implemented System

The current system includes:

- service-class-aware digital twin for eMBB, URLLC, mMTC, FWA, and V2X
- normalized KPI ingestion from simulated, Open RAN KPM, OAI-style, and FlexRIC KPM sources
- anomaly detection, RCA, healing recommendation, and guarded automation
- xApp-style JSONL decision output
- SQLite decision and feature-row audit store
- Open RAN KPM dataset import, weak-label training, overfitting checks, and held-out context benchmarks
- localhost dashboard for scenario control and live status
- PowerShell wrappers for OAI/FlexRIC collection and evidence pipeline execution

## Latest FlexRIC KPM Evidence

Latest strong run:

```text
Run name: flexric_kpm_30min
Report: outputs/reports/flexric_kpm_30min.json
Training summary: data/training/flexric_kpm_30min_augmented_training.summary.json
Model: outputs/models/flexric_kpm_30min_self_learning_model.json
Benchmark: outputs/benchmarks/flexric_kpm_30min_ml_benchmark.json
Balanced benchmark: outputs/benchmarks/flexric_kpm_30min_ml_benchmark_balanced.json
```

Observed evidence:

| Metric | Value |
|---|---:|
| JSONL decision records | 71,900 |
| SQLite decision records | 71,900 |
| SQLite feature rows | 87,927 |
| Data quality events | 0 |
| Normal decisions | 71,532 |
| Anomaly decisions | 368 |
| Main detected root cause | backhaul_degradation |
| Main healing action | reroute_transport_path |
| Automation decision for anomalies | allow_with_monitoring |
| RIC control output for anomalies | a1_policy |

Training data created from the run:

| Metric | Value |
|---|---:|
| Base live/lab KPM rows | 73,692 |
| Augmented training rows | 442,152 |
| Scenarios per base row | 6 |
| Fault scenario types | cell_congestion, backhaul_degradation, radio_link_degradation, packet_loss_degradation, handover_instability |

## What The Evidence Proves

This proves that:

1. FlexRIC KPM monitor output can be collected from the lab path.
2. KPM rows can be converted into the project KPI schema.
3. The shared decision engine can process sustained KPM telemetry.
4. Decisions are written both as xApp-style JSONL and SQLite audit records.
5. The pipeline can create training artifacts, train a local self-learning model, and benchmark it.

## Honest Boundaries

The current evidence does not yet prove production-grade self-healing because:

- live/lab normal rows are not the same as operator production traffic
- fault rows in the augmented FlexRIC training set are controlled synthetic perturbations
- current live telemetry does not include independent operator-validated fault truth
- the 30-minute benchmark holdout used only a fault scenario unless the balanced holdout mode is enabled
- real E2 actuation, rollback governance, auth, deployment operations, and longer observability windows are still future work

## Balanced Benchmark Check

The balanced 30-minute benchmark keeps the radio-link-degradation scenario as the held-out fault case, but also places normal rows in the test split.

```text
python scripts\benchmark_ml_models.py --input data\training\flexric_kpm_30min_augmented_training.csv --output outputs\benchmarks\flexric_kpm_30min_ml_benchmark_balanced.json --holdout-column scenario --holdout-value radio_link_degradation --include-normal-holdout
```

Balanced split:

| Split | Records | Fault rows | Normal rows |
|---|---:|---:|---:|
| Train | 18,750 | 16,666 | 2,084 |
| Test | 6,250 | 4,167 | 2,083 |

Selected result:

| Model | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|
| Online self-learning v1 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Full guarded decision engine sample | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Isolation Forest | 0.9509 | 1.0000 | 0.9748 | 0.1032 |

Interpretation: this is a better evidence artifact than the original fault-only holdout because it includes true negatives and false-positive-rate measurement. The supervised Random Forest and Gradient Boosting baselines still perform poorly on this held-out-fault split because `radio_link_degradation` is absent from supervised training. The guarded engine and online self-learning path perform well because they use physical KPI signatures and normal-baseline deviation logic. The caveat remains that the fault rows are controlled synthetic perturbations over live/lab KPM normal rows.

## Controlled Fault-Injection Evaluation

A timestamped fault-injection evaluator now creates an answer key, injects controlled faults into normalized FlexRIC KPM rows, runs the decision engine, and exports decision-level CSV evidence.

Command:

```powershell
python tools\controlled_fault_injection_evaluation.py --input outputs\flexric_xapp_longrun_normalized.csv --run-name controlled_fault_eval_30min --max-rows 2400 --schedule-output outputs\evidence\controlled_fault_schedule.csv --labelled-output outputs\evidence\controlled_fault_injected_telemetry.csv --decisions-output outputs\evidence\controlled_fault_decisions.csv --report-output outputs\evidence\controlled_fault_evaluation.json
```

Artifacts:

```text
outputs/evidence/controlled_fault_schedule.csv
outputs/evidence/controlled_fault_injected_telemetry.csv
outputs/evidence/controlled_fault_decisions.csv
outputs/evidence/controlled_fault_evaluation.json
outputs/evidence/controlled_fault_evaluation.md
```

Schedule:

| Window | Fault | Start | End | Expected healing |
|---|---|---:|---:|---|
| fault_001 | backhaul_degradation | 300 | 600 | reroute_transport_path |
| fault_002 | packet_loss_degradation | 780 | 1080 | reroute_transport_path |
| fault_003 | cell_congestion | 1260 | 1560 | load_balance_neighbor_cell |
| fault_004 | radio_link_degradation | 1740 | 2040 | dynamic_spectrum_reassignment |
| fault_005 | handover_instability | 2160 | 2340 | rrc_mobility_policy_tuning |

Result:

| Metric | Value |
|---|---:|
| Records | 2,400 |
| Fault windows | 5 |
| True positives | 1,380 |
| True negatives | 1,020 |
| False positives | 0 |
| False negatives | 0 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1-score | 1.0000 |
| False-positive rate | 0.0000 |
| RCA accuracy when detected | 0.8761 |
| Healing accuracy when detected | 0.8761 |

Interpretation: this gives the project a lab-style correctness check with explicit timestamps and expected fault labels. It is stronger than unlabeled live telemetry, but it is still controlled replay validation rather than independent operator fault truth.

## 30-Minute vs 2-Hour Run

A 30-minute run is enough for a credible milestone, demo, and resume artifact. It shows sustained ingestion, repeatable processing, and zero data-quality events.

A 2-hour run is better for a final public claim because it gives stronger evidence for:

- long-running stability
- SQLite growth and decision throughput
- repeated anomaly handling
- drift monitor behavior after warm-up
- absence of parser/data-quality degradation over time

Recommended claim levels:

| Run length | Best use |
|---|---|
| 5 minutes | smoke proof and quick demo |
| 30 minutes | strong milestone evidence |
| 2 hours | final showcase evidence |
| 6-24 hours | research-grade stability evidence |

## Next Validation Step

Run the 2-hour pipeline when machine time is available:

```powershell
.\scripts\run_kpm_evidence_pipeline.ps1 -DurationSeconds 7200 -RunName flexric_kpm_2hr -SkipPatch
```

Then run the balanced benchmark:

```powershell
python scripts\benchmark_ml_models.py --input data\training\flexric_kpm_2hr_augmented_training.csv --output outputs\benchmarks\flexric_kpm_2hr_ml_benchmark_balanced.json --holdout-column scenario --holdout-value radio_link_degradation --include-normal-holdout
```

## Resume Framing

Use this version:

```text
Built an AI-native self-healing O-RAN digital twin with FlexRIC KPM telemetry ingestion, xApp-style JSONL decisions, RCA, guarded healing, SQLite audit evidence, Open RAN KPM benchmarking, and a live dashboard. Validated a 30-minute FlexRIC KPM run with 71.9K decisions, 87.9K stored feature rows, zero data-quality events, and automated backhaul-degradation mitigation recommendations.
```

## Monetizable Direction

The strongest product direction is:

```text
RAN Assurance Copilot / xApp Safety Sandbox
```

Target users:

- telecom labs testing xApps before deployment
- students/research teams needing reproducible O-RAN evidence
- private 5G teams validating self-healing rules
- vendors needing demoable RIC/SMO assurance workflows

Potential paid version:

- managed dashboard
- dataset replay packs
- policy safety scorecards
- fault-injection templates
- xApp decision audit export
- SLA/customer-impact reports
