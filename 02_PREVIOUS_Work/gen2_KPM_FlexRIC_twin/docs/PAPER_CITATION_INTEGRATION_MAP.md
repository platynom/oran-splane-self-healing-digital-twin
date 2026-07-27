# Paper Citation And Integration Map

This file explains which papers, standards, and datasets influenced the project and where each idea was integrated.

## Core Standards And Architecture

| Source | Why it was used | Integrated into |
|---|---|---|
| ETSI TS 103 982, O-RAN Architecture Description | Defines O-RAN architecture, SMO, RIC, O-CU/O-DU/O-RU, and open interface context. | `README.md`, `xapp_runner.py`, `oran_twin/engine.py`, `configs/topology.json` |
| ETSI TS 123 501, 5G System Architecture | Provides 5G system architecture, slicing, AMF/UPF/PDU-session context, and N3/N6 transport concepts. | `oran_twin/core_transport.py`, `oran_twin/slice_impact.py`, `configs/slice_sla_profiles.json` |
| ETSI TS 138 401, NG-RAN Architecture | Provides gNB, CU/DU split, NG-RAN function placement, and RAN interface context. | `configs/topology.json`, `oran_twin/timing_security.py`, `oran_twin/telemetry_adapters.py` |
| ETSI TS 133 501, 5G Security | Provides 5G authentication/security framing and risk considerations. | `oran_twin/security_guard.py`, `configs/aml_attack_scenarios.json` |
| ETSI GR ZSM 015, Digital Twin Networks | Motivates zero-touch management and digital twin network concepts. | `oran_twin/dtn_orchestrator.py`, `oran_twin/policy_orchestrator.py`, `configs/zsm_policy_profiles.json` |

## O-RAN, RIC, xApp, And Automation Papers

| Source | Why it was used | Integrated into |
|---|---|---|
| Polese et al., Understanding O-RAN Architecture, Interfaces, Algorithms, Security, and Research Challenges | Background for O-RAN interfaces, RIC/xApp design, and security concerns. | `docs/OAI_FLEXRIC_OPTION2_SETUP.md`, `xapp_runner.py`, `oran_twin/engine.py` |
| Elsevier 2025 O-RAN xApps Survey and Research Challenges | Motivates xApp use cases, traffic steering, load balancing, slicing, and AI/ML control. | `oran_twin/engine.py`, `oran_twin/conflict_manager.py`, `scripts/benchmark_xapp_arbitration.py` |
| ACM 2025 xApp Direct Conflict Detection and Mitigation in Testbed | Motivates xApp conflict detection and mitigation. | `oran_twin/conflict_manager.py`, `configs/xapp_distillation_policy.json`, `outputs/benchmarks/xapp_arbitration_benchmark.json` |
| Elsevier 2026 xApp Distillation for Conflict Mitigation | Motivates teacher/student style xApp arbitration. | `oran_twin/conflict_manager.py`, `configs/xapp_distillation_policy.json` |
| Elsevier 2025 dApps Real-Time AI Open RAN Control | Supports AI-native real-time control direction and RIC-ready runtime design. | `xapp_runner.py`, `tools/stream_live_oai_to_engine.py`, `scripts/run_kpm_evidence_pipeline.ps1` |

## Digital Twin And AI-Native Networking

| Source | Why it was used | Integrated into |
|---|---|---|
| O-RAN Digital Twin RAN Use Cases | Supports using a digital twin to mirror RAN state and validate actions before execution. | `oran_twin/digital_twin.py`, `oran_twin/pipeline.py`, `docs/FINAL_EVIDENCE_REPORT.md` |
| O-RAN Research Report 2024-09, Digital Twin RAN Key Enablers | Supports twin synchronization, telemetry, and control-loop design. | `oran_twin/dtn_orchestrator.py`, `live_backend.py` |
| IEEE 2024 AI-Enabled Digital Twin Network in 6G Survey | Motivates AI-enabled network digital twin architecture. | `oran_twin/dtn_orchestrator.py`, `configs/dtn_capability_profiles.json` |
| IEEE 2025 Network Digital Twin for 6G and Beyond | Supports end-to-end network twin and assurance concepts. | `oran_twin/slice_impact.py`, `oran_twin/core_transport.py` |
| Springer 2024 LLM Twin Beyond 5G DTN | Used as future-facing DTN/AI orchestration context, not implemented as an LLM controller. | `oran_twin/dtn_orchestrator.py`, `docs/FINAL_EVIDENCE_REPORT.md` |

## AI/ML, Drift, And Anomaly Detection

| Source | Why it was used | Integrated into |
|---|---|---|
| Elsevier 2024 Drift Handling Framework for Open RAN | Motivates model drift monitoring and lifecycle controls. | `oran_twin/drift_monitor.py`, `oran_twin/automation_safety.py` |
| IEEE 2024 Federated Continual Learning O-RAN Anomaly Detection | Supports continual/self-learning anomaly detection direction. | `oran_twin/self_learning.py`, `scripts/train_self_learning_model.py` |
| IEEE 2025 Anomaly Detection for xApp and E2 Interface Threats in O-RAN | Motivates E2/KPM anomaly signatures and security-aware anomaly handling. | `oran_twin/engine.py`, `oran_twin/security_guard.py` |
| IEEE 2024 AI-Based Anomaly Detection for Industrial 5G by Distributed SDR Measurements | Supports KPI-driven anomaly detection using radio/network measurements. | `tools/normalize_telemetry.py`, `tools/controlled_fault_injection_evaluation.py` |
| Elsevier 2023 OpenRAN Gym AI/ML for O-RAN | Used as background for AI/ML experimentation and reproducible O-RAN control-loop evaluation. | `scripts/benchmark_ml_models.py`, `outputs/benchmarks/` |

## Security, AML, And Safe Automation

| Source | Why it was used | Integrated into |
|---|---|---|
| Elsevier 2024 Adversarial Machine Learning Threat Analysis and Remediation in O-RAN | Motivates AML threat scenarios and guarded automation. | `oran_twin/security_guard.py`, `configs/aml_attack_scenarios.json`, `oran_twin/automation_safety.py` |
| arXiv ZT-RIC Zero Trust RIC Framework | Supports zero-trust RIC/xApp thinking. | `oran_twin/security_guard.py`, `oran_twin/policy_orchestrator.py` |
| BSI 5G RAN Risk Analysis | Used for high-level 5G RAN risk framing. | `oran_twin/security_guard.py`, `configs/aml_attack_scenarios.json` |
| Springer 2025 CERBERUS Secure Automated Multi-Operator Management in B5G ZSM | Motivates secure ZSM workflow, tenant/operator context, and audit gates. | `oran_twin/policy_orchestrator.py`, `oran_twin/smo_governance.py`, `configs/zsm_policy_profiles.json` |
| Springer 2025 TSN Digital Twin for STRIDE-Based Security Testing | Motivates timing/PTP security twin and STRIDE-style timing checks. | `oran_twin/timing_security.py`, `configs/timing_security_profiles.json` |

## Spectrum, Slicing, And RAN Resource Assurance

| Source | Why it was used | Integrated into |
|---|---|---|
| ACM 2024 SpotLight Open RAN System for Dynamic Spectrum Access and Anomaly Detection | Motivates spectrum/resource anomaly monitor and dynamic spectrum policy output. | `oran_twin/spectrum_monitor.py`, `configs/spectrum_access_profiles.json` |
| IEEE 2024 Digital Twin-Driven End-to-End Network Slicing Toward 6G | Motivates slice/SLA impact twin and E2E slice assurance. | `oran_twin/slice_impact.py`, `configs/slice_sla_profiles.json` |
| IEEE 2025 RADAR Robust DRL-Based Resource Allocation Against Adversarial Attacks in O-RAN | Used as background for robust resource allocation under adversarial conditions. | `oran_twin/security_guard.py`, `oran_twin/automation_safety.py` |

## Datasets And Evidence Sources

| Source | Why it was used | Integrated into |
|---|---|---|
| Open RAN Commercial Traffic Twinning dataset | Provides realistic KPM-style traffic/slicing data for training and replay benchmarking. | `tools/import_openran_kpm_dataset.py`, `scripts/benchmark_ml_models.py`, `docs/FINAL_EVIDENCE_REPORT.md` |
| FlexRIC KPM monitor output | Provides lab/live KPM evidence beyond synthetic simulation. | `scripts/run_kpm_evidence_pipeline.ps1`, `tools/oai_metric_bridge.py`, `outputs/reports/flexric_kpm_30min.json` |
| Controlled timestamped fault injection over FlexRIC-normalized rows | Provides labelled answer-key validation for detection, RCA, and healing correctness. | `tools/controlled_fault_injection_evaluation.py`, `outputs/evidence/controlled_fault_evaluation.md` |

## AI/ML Models Actually Used

The project uses AI/ML at prototype level:

- online self-learning statistical model in `oran_twin/self_learning.py`
- Isolation Forest benchmark in `scripts/benchmark_ml_models.py`
- Random Forest benchmark in `scripts/benchmark_ml_models.py`
- Gradient Boosting benchmark in `scripts/benchmark_ml_models.py`
- baseline anomaly scoring and drift monitoring in `oran_twin/detector.py` and `oran_twin/drift_monitor.py`

The project does not yet use deep neural networks in the active decision path. If asked, describe it as:

```text
AI/ML-based anomaly detection, online self-learning, and benchmarked classical ML models, with deep learning deferred for future work.
```
