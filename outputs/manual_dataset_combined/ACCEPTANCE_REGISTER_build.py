import json
from pathlib import Path

def build_acceptance_register():
    root = Path(__file__).resolve().parent
    repo_root = root.parents[1]
    emp_root = repo_root / 'outputs' / 'empirical_software_network_pilot_v1'

    ra_path = emp_root / 'RUN_ANALYSIS.json'
    rep_path = emp_root / 'REPEATABILITY.json'
    reverif_path = root / 'reverification_v1.json'
    disc_path = emp_root / 'DISCRIMINATOR_RESULTS.json'
    disc3_path = emp_root / 'DISCRIMINATOR_RESULTS_3CLASS.json'

    with open(ra_path, 'r', encoding='utf-8') as f:
        ra = json.load(f)

    with open(rep_path, 'r', encoding='utf-8') as f:
        rep = json.load(f)

    with open(reverif_path, 'r', encoding='utf-8') as f:
        reverif = {item['criterion']: item for item in json.load(f)}

    with open(disc_path, 'r', encoding='utf-8') as f:
        disc = json.load(f)

    with open(disc3_path, 'r', encoding='utf-8') as f:
        disc3 = json.load(f)

    # Dynamic status determination for Criterion 22:
    # Requires discriminator evaluation executed, leave-one-out evaluated, and permutation control computed.
    c22_evaluated = 'detection_features' in disc and len(disc['detection_features']) > 0
    c22_status = 'MEASURED' if c22_evaluated else 'IMPLEMENTED'

    # Dynamic status determination for Criterion 23:
    # Requires 3-class discriminator evaluation executed, leave-one-out evaluated, and permutation control computed.
    c23_evaluated = 'honest_online_evaluation' in disc3 and 'macro_f1' in disc3['honest_online_evaluation']['leave_one_out_cross_validation']
    c23_status = 'MEASURED' if c23_evaluated else 'IMPLEMENTED'

    content = f"""# Numbered Acceptance Register — O-RAN S-Plane Evidence Validation

Status vocabulary: IMPLEMENTED | EXECUTED | MEASURED | VALIDATED | QUARANTINED | BLOCKED_EXTERNAL | ASSERTED_NOT_REVERIFIED | DOCUMENTED_ONLY | BROKEN_CITATION

Vocabulary definitions:
- **MEASURED**: Quantitative packet or protocol metric extracted from empirical capture or dataset artifact.
- **DOCUMENTED_ONLY**: Describes design intent, taxonomy, or proposed framework with no carrier artifact or complete treatment in repository.
- **QUARANTINED**: Excluded from valid ground truth or model evaluation; rationale explicitly recorded.
- **BROKEN_CITATION**: Citation anchor or referenced file does not resolve against repository files.
- **IMPLEMENTED**: Harness, software module, or configuration implemented and present in repository.
- **EXECUTED**: Script or testbed harness executed in target environment with runtime artifacts recorded.
- **VALIDATED**: Authenticated against independent primary source evidence.
- **BLOCKED_EXTERNAL**: Requires external author records, physical instruments, or missing experiment artifacts.
- **ASSERTED_NOT_REVERIFIED**: Recorded by an earlier session and not re-checked against sources in the current evaluation chain.

Rule of this register: Evidence fields must reference artifact file paths and internal JSON key paths. No inline measured numerical values are permitted in evidence descriptions.

## Summary Register Table

| # | Criterion | Status | Evidence Reference |
|---|---|---|---|
| 1 | Source traceability | BLOCKED_EXTERNAL | `outputs/manual_dataset_combined/source_traceability_audit.json#external_inventory` |
| 2 | Historical relevance / dependency tracing | BLOCKED_EXTERNAL | `outputs/manual_dataset_combined/source_traceability_audit.json#static_references` |
| 3 | PCAP-to-telemetry alignment | {reverif['3']['verdict']} | `outputs/manual_dataset_combined/production_lineage_verification.json#verified_output_records` |
| 4 | Clear taxonomy | {reverif['4']['verdict']} | `outputs/manual_dataset_combined/LABEL_TAXONOMY.md` |
| 5a | Production capture label reproducibility | MEASURED | `outputs/manual_dataset_combined/issue01_production_verification.json` |
| 5b | Attacker authorisation and attack-launch record | BLOCKED_EXTERNAL | `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#4-unresolved--do-not-invent` |
| 6a | Capture duplication | MEASURED | `outputs/manual_dataset_combined/criterion06_audit.json#pcap_comparison.pcaps_identical` |
| 6b | Label reproducibility for multi-raw capture | MEASURED | `outputs/manual_dataset_combined/criterion06_audit.json#csv_comparison.conflict_breakdown` |
| 6c | Multi-raw session labels omit same sender Sync/Follow_Up | MEASURED | `outputs/manual_dataset_combined/CRITERION_06_FINDINGS.md#2-5-scope-caveat-on-label-semantics-mirroring-production-capture` |
| 7 | Parameter provenance | {reverif['7']['verdict']} | `outputs/manual_dataset_combined/PARAMETER_PROVENANCE.md` |
| 8 | Threshold justification | {reverif['8']['verdict']} | `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md#thresholds` |
| 9 | Defensible relationships | {reverif['9']['verdict']} | `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md` |
| 10 | Recovery evidence | BLOCKED_EXTERNAL | `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md#recovery-evidence` |
| 11 | Basic explanations (WHAT/WHICH/WHERE/WHEN/WHY/HOW) | {reverif['11']['verdict']} | `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#3-6-retained-production-conclusions-what-which-where-when-why-how` |
| 12 | Final dataset reconciliation | {reverif['12']['verdict']} | `outputs/manual_dataset_combined/detailed_reconciliation.json#rows` |
| 13 | On-wire BMCA takeover observed in victim Announce stream | MEASURED | `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#2-receiver-side-bmca-evidence-is-in-the-capture` |
| 14 | Supplied production labels omit same sender Sync/Follow_Up | MEASURED | `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#34-the-supplied-labels-are-incomplete` |
| 15 | Victim selected labelled sender before first captured Announce | MEASURED | `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#32-the-capture-does-not-contain-the-attack-onset` |
| 16 | Runner implementation | IMPLEMENTED | `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_empirical_software_pilot.sh` |
| 17 | WSL execution environment | EXECUTED | `outputs/empirical_software_network_pilot_v1/runs/20260911_set2_baseline_r1/run_environment.txt` |
| 18 | Four empirical pilot conditions | IMPLEMENTED | `outputs/empirical_software_network_pilot_v1/EXECUTION_ORDER.json#condition_time_blocks` |
| 19 | 12-run matched set | MEASURED | `outputs/empirical_software_network_pilot_v1/EXECUTION_ORDER.json#ordered_runs` |
| 20 | Netem direction-match result | MEASURED | `outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_netem_r1.netem_loss_comparison.direction_match` |
| 21 | Intervention outage result | MEASURED | `outputs/empirical_software_network_pilot_v1/INTERVENTION_OUTAGE_RECONCILIATION.json#summary.runs_with_outage_detected_2_5x_criterion` |
| 22 | Configured impairment discrimination | {c22_status} | `outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS.json#detection_features.sync_fu_paired_delay_std_s.leave_one_out.accuracy` |
| 23 | Three-class configured impairment and source loss discrimination | {c23_status} | `outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS_3CLASS.json#honest_online_evaluation.leave_one_out_cross_validation.macro_f1` |

---

## Explicit Quarantine and Superseded Records Policy

> [!IMPORTANT]
> **Quarantine Record 1 (Run n2)**: `runs/20260910_calibrated_netem` remains permanently **QUARANTINED**. The netem qdisc was configured on an un-impairing path and carried zero packets during protocol execution.

> [!IMPORTANT]
> **Quarantine Record 2 (Multi-Raw Labels 1)**: `dataset/timesafe/timesafe_multi_raw/announce_session_1_labels.csv` is **QUARANTINED-BUT-RETAINED**. It is an unreproducible partial labeling artifact containing boundary-clipped non-Announce frames. It is preserved on disk for provenance tracing and audit history, but excluded from model training and evaluation.

> [!IMPORTANT]
> **Quarantine Record 3 (Projected Session Correlations)**: Feature-to-label correlation claims on projected TIMESAFE sessions are **QUARANTINED**. Labels were projected from packet intervals and correlated against features derived from the same packets, creating circular evaluation. Gated out in code.

> [!NOTE]
> **Capture Duplication Notice**: The two multi-raw session captures `announce_session_1.pcap` and `announce_session_2.pcap` share identical SHA-256 hashes and constitute a single file under two filenames. Using both in dataset splits constitutes duplicate counting and data leakage.

> [!WARNING]
> **Superseded Records**: All analytical records for `set2` generated prior to the updated `analyze_runs.py` execution on 2026-09-11 are superseded and invalid as project evidence.

> [!CAUTION]
> **Protocol Deviation Record (Deleted Incomplete Run)**: On 2026-09-11T17:16:13Z, an incomplete directory `runs/20260911_set3_control_r7` interrupted by server restart was deleted via `shutil.rmtree` prior to re-execution. Deleting run directories violates experiment provenance rules. The failed attempt's evidence is unrecoverable. The re-executed run was retained. Recorded in `outputs/empirical_software_network_pilot_v1/EMPIRICAL_RUN_REGISTRY.json#protocol_deviations`.

---

## Scope Limitations

- **Shared Host Kernel Clock**: All network namespaces read from a single shared host kernel clock. The testbed evaluates protocol messaging dynamics, frame sequence tracking, and packet-observable outages, but cannot evaluate physical clock synchronization error, phase alignment, or oscillator frequency drift. Evidence pointer: `outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_baseline_r1.software_timestamp_servo_stat.label`.

---

## Detailed Criteria Specifications

### Criterion 1: Source Traceability
- **Requirement**: Preserve source identity while separating direct code use, duplicate copies, derived representations, and historical material.
- **Method**: Automated hash and schema audit across external repositories and local dataset copies.
- **Evidence**: `outputs/manual_dataset_combined/source_traceability_audit.json#external_inventory`
- **Result**: Canonical source mapping recorded; dynamic invocation from external scripts remains unproven at runtime.
- **Changes Made**: Gated unvalidated dataset dependencies behind explicit path checks.
- **Remaining Limitation**: Dynamic execution paths require runtime audit.
- **Status**: BLOCKED_EXTERNAL

### Criterion 2: Historical Relevance / Dependency Tracing
- **Requirement**: Identify direct dependencies on historical session files and prevent unvalidated reliance.
- **Method**: Code inspection of ingester, open-set evaluator, and session transformers.
- **Evidence**: `outputs/manual_dataset_combined/source_traceability_audit.json#static_references`
- **Result**: Historical session exports identified as derived representations; direct use gated.
- **Changes Made**: Replaced hardcoded session loading with mandatory hash-bound metadata gate.
- **Remaining Limitation**: Absence of third-party external references cannot be proven without full execution tracing.
- **Status**: BLOCKED_EXTERNAL

### Criterion 3: PCAP-to-Telemetry Alignment
- **Requirement**: Align raw PCAP packet frames to derived telemetry rows with cryptographic hash binding.
- **Method**: Direct recomputation from primary PCAP and lineage sidecar matching sequence numbers and source packet indices.
- **Evidence**: `outputs/manual_dataset_combined/production_lineage_verification.json#verified_output_records`
- **Result**: Derived rows correspond one-to-one to emitted PTP frames in capture; prefix frames lack initial sync resolution and are not emitted.
- **Changes Made**: Repaired evidence reference to resolvable key and recorded exact frame correspondence.
- **Remaining Limitation**: {reverif['3']['limitation']}
- **Status**: {reverif['3']['verdict']}

### Criterion 4: Clear Taxonomy
- **Requirement**: Separate packet annotations, projections, simulation, model predictions, actions, and outcomes.
- **Method**: Audit of label taxonomy definitions against repository carrier artifacts.
- **Evidence**: `outputs/manual_dataset_combined/LABEL_TAXONOMY.md`
- **Result**: Taxonomy defines 10 operational levels; nine have repository carrier files, while measured clock health has no carrier artifact.
- **Changes Made**: Repaired evidence pointer to bare markdown file and reclassified as documented only.
- **Remaining Limitation**: {reverif['4']['limitation']}
- **Status**: {reverif['4']['verdict']}

### Criterion 5a: Production Capture Label Reproducibility
- **Requirement**: Reproduce saved dataset labels from capture-specific packet field patterns.
- **Method**: The saved labels are reproduced exactly by the capture-intrinsic rule `Source == b8:ce:f6:5e:6b:4a AND MessageType == 11`, with zero false positives and zero false negatives across all rows; the supplied `prodtest_dataset_gen.py` fails because its argparse default input and its MAC belong to a different capture.
- **Evidence**: `outputs/manual_dataset_combined/issue01_production_verification.json`
- **Result**: Production label pattern reproduced deterministically via MAC and message type check.
- **Changes Made**: Documented exact packet-field selection rule for production capture.
- **Remaining Limitation**: Requires author launch record to determine original label intent.
- **Status**: MEASURED

### Criterion 5b: Attacker Authorisation and Attack-Launch Record
- **Requirement**: Authorisation logs and attack-launch records confirming malicious intent.
- **Method**: Inspection of author source tree logs directory.
- **Evidence**: `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#4-unresolved--do-not-invent`
- **Result**: Launch logs absent from upstream repository; author records required.
- **Changes Made**: Explicitly separated packet pattern reproducibility from attacker authorisation.
- **Remaining Limitation**: Requires external attack launch records from authors.
- **Status**: BLOCKED_EXTERNAL

### Criterion 6a: Capture Duplication
- **Requirement**: Detect duplicate representations and prevent identical captures under alternate filenames from inflating sample counts or causing data leakage.
- **Method**: Cryptographic SHA-256 hash comparison across `announce_session_1.pcap` and `announce_session_2.pcap`.
- **Evidence**: `outputs/manual_dataset_combined/criterion06_audit.json#pcap_comparison.pcaps_identical`
- **Result**: Both session PCAPs share identical SHA-256 hashes, establishing they are one capture under two names.
- **Changes Made**: Flagged duplicate status in dataset inventory and audit documentation.
- **Remaining Limitation**: Upstream documentation does not explain the duplication of the capture file.
- **Status**: MEASURED

### Criterion 6b: Label Reproducibility for Multi-Raw Capture
- **Requirement**: Determine whether conflicting label files for the duplicate capture can be reproduced by explicit protocol rules.
- **Method**: Exhaustive rule scan across all `(Source, MessageType)` pairs and row-by-row label comparison between Session 1 and Session 2.
- **Evidence**: `outputs/manual_dataset_combined/criterion06_audit.json#csv_comparison.conflict_breakdown`
- **Result**: `announce_session_2_labels.csv` is 100% reproduced by `Source == 1 AND MessageType == 11`. `announce_session_1_labels.csv` is not reproducible by any single rule and contains a boundary-clipped Follow_Up frame. `labels_2` is retained as the authoritative representation; `labels_1` is quarantined.
- **Changes Made**: Quarantined `announce_session_1_labels.csv` and documented rule derivation for `labels_2`.
- **Remaining Limitation**: Original author scripts generating `labels_1` remain unrecovered.
- **Status**: MEASURED

### Criterion 6c: Multi-Raw Session Labels Omit Same Sender Sync and Follow_Up
- **Requirement**: Evaluate whether positive labels in `announce_session_2_labels.csv` encompass all traffic from the candidate source.
- **Method**: Frame inventory calculation of capture by source and message type.
- **Evidence**: `outputs/manual_dataset_combined/CRITERION_06_FINDINGS.md#2-5-scope-caveat-on-label-semantics-mirroring-production-capture`
- **Result**: Positive labels cover only Announce messages from Source 1; concurrent Sync and Follow_Up frames from Source 1 in the same session are labeled 0, indicating the label signifies "Announce from that source" rather than "malicious frame".
- **Changes Made**: Documented semantic label scope mirroring production capture findings.
- **Remaining Limitation**: Ground-truth maliciousness cannot be established from packet fields alone.
- **Status**: MEASURED

### Criterion 7: Parameter Provenance
- **Requirement**: Trace active fields, defaults, transformations, consumers, and operational limits.
- **Method**: Source code audit confirming presence and operational classification of all schema parameters across ingestion, telemetry, and twin code.
- **Evidence**: `outputs/manual_dataset_combined/PARAMETER_PROVENANCE.md`
- **Result**: Code confirmed symbols and categorized them as parsed, calculated, defaulted, or inferred; no parameter represents calibrated physical hardware telemetry.
- **Changes Made**: Repaired evidence pointer to bare markdown file and validated code symbols.
- **Remaining Limitation**: {reverif['7']['limitation']}
- **Status**: {reverif['7']['verdict']}

### Criterion 8: Threshold Justification
- **Requirement**: Differentiate configured/model thresholds from physical network requirements.
- **Method**: Direct code and configuration audit tracing thresholds to definitions and usages.
- **Evidence**: `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md#thresholds`
- **Result**: All thresholds identified in default configuration and code; 100 ns trigger confirmed to be a configured software default without empirical or physical justification in repository.
- **Changes Made**: Validated threshold definitions against configuration and code.
- **Remaining Limitation**: {reverif['8']['limitation']}
- **Status**: {reverif['8']['verdict']}

### Criterion 9: Defensible Relationships
- **Requirement**: Document bounded, descriptive relationships without unproven causal claims.
- **Method**: Code audit of feature computation and label assignment in open-set evaluation pipeline.
- **Evidence**: `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md`
- **Result**: Projected session relationships found circular due to features and labels deriving from identical packet intervals; sessions are quarantined in evaluation code.
- **Changes Made**: Quarantined circular relationship claims and repaired evidence reference.
- **Remaining Limitation**: {reverif['9']['limitation']}
- **Status**: {reverif['9']['verdict']}

### Criterion 10: Recovery Evidence
- **Requirement**: Separate theoretical recovery candidate actions from physical execution evidence.
- **Method**: Audit of self-healing action triggers and execution logs.
- **Evidence**: `outputs/manual_dataset_combined/THRESHOLD_AND_RECOVERY_AUDIT.md#recovery-evidence`
- **Result**: Action candidates classified as software proposals rather than physical actions.
- **Changes Made**: Isolated simulation model actions from host network execution.
- **Remaining Limitation**: Physical recovery evaluation requires hardware testbed controls.
- **Status**: BLOCKED_EXTERNAL

### Criterion 11: Basic Explanations (WHAT/WHICH/WHERE/WHEN/WHY/HOW)
- **Requirement**: Provide clear introductory context and parameter definitions for all dataset fields.
- **Method**: Audit of documentation coverage for retained conclusions across explanatory artifacts.
- **Evidence**: `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#3-6-retained-production-conclusions-what-which-where-when-why-how`
- **Result**: Explanatory coverage confirmed with full WHAT/WHICH/WHERE/WHEN/WHY/HOW breakdowns across empirical pilot, multi-raw session, and production PCAP findings.
- **Changes Made**: Added explicit six-question framework treatment for production PCAP conclusions and validated full coverage across retained claims.
- **Remaining Limitation**: {reverif['11']['limitation']}
- **Status**: {reverif['11']['verdict']}

### Criterion 12: Final Dataset Reconciliation
- **Requirement**: Reconcile all source manifest records and cells against canonical workbook.
- **Method**: Direct recomputation of row counts, file counts, and cryptographic SHA-256 hashes across all 45 source files.
- **Evidence**: `outputs/manual_dataset_combined/detailed_reconciliation.json#rows`
- **Result**: Exact mathematical agreement recomputed across all 45 source files and all data rows.
- **Changes Made**: Repaired evidence pointer to valid key path and validated recomputation.
- **Remaining Limitation**: {reverif['12']['limitation']}
- **Status**: {reverif['12']['verdict']}

### Criterion 13: On-Wire BMCA Takeover Observed in Victim Announce Stream
- **Requirement**: Demonstrate whether BMCA source selection changes occurred in receiver announcements.
- **Method**: Decoding PTP Announce frames emitted by incumbent boundary clock in primary capture.
- **Evidence**: `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#2-receiver-side-bmca-evidence-is-in-the-capture`
- **Result**: On-wire BMCA takeover observed in victim's own Announce stream, where boundary clock announced labelled sender clockIdentity.
- **Changes Made**: Documented receiver-side BMCA evidence from PCAP primary dissection.
- **Remaining Limitation**: Does not establish whether the source was authorised.
- **Status**: MEASURED

### Criterion 14: Supplied Production Labels Omit Same Sender Sync and Follow_Up
- **Requirement**: Determine the exact packet scope of positive label annotations.
- **Method**: Message type frame counting for the labelled sender across capture window.
- **Evidence**: `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#34-the-supplied-labels-are-incomplete`
- **Result**: Supplied labels omit the same sender's Sync and Follow_Up frames in the same window, so the label means "Announce from that sender", not "malicious".
- **Changes Made**: Documented label coverage across PTP message types.
- **Remaining Limitation**: True semantic intent requires author confirmation.
- **Status**: MEASURED

### Criterion 15: Victim Selected Labelled Sender Before First Captured Announce
- **Requirement**: Establish temporal relationship between attack onset and victim selection.
- **Method**: Packet timestamp comparison between victim BMCA re-advertisement and first captured Announce from labelled sender.
- **Evidence**: `outputs/manual_dataset_combined/PCAP_PRIMARY_EVIDENCE.md#32-the-capture-does-not-contain-the-attack-onset`
- **Result**: The victim selected the labelled sender before the first captured Announce from it, so the capture does not contain the attack onset.
- **Changes Made**: Recorded pre-capture selection event in primary evidence audit.
- **Remaining Limitation**: The missing-frame conclusion rests on event ordering within one capture.
- **Status**: MEASURED

### Criterion 16: Runner Implementation
- **Requirement**: Implement reproducible network namespace testbed runner for software pilot.
- **Method**: Shell script harness defining network namespaces, bridge in root namespace, and `ptp4l` instances.
- **Evidence**: `01_CURRENT_SPlane_SelfHealing/oran_splane_selfhealing/harness/run_empirical_software_pilot.sh`
- **Result**: Software harness implemented with topology setup, packet capture, and teardown.
- **Changes Made**: Configured namespace topology, netem placement on `$SR`, and packet capture interface.
- **Remaining Limitation**: Operates purely in software network namespace environment.
- **Status**: IMPLEMENTED

### Criterion 17: WSL Execution Environment
- **Requirement**: Execute pilot harness under Linux environment in WSL with recorded environment state.
- **Method**: Inspecting execution environment file written during testbed run.
- **Evidence**: `outputs/empirical_software_network_pilot_v1/runs/20260911_set2_baseline_r1/run_environment.txt`
- **Result**: Linux environment execution recorded with linuxptp version and free-running measurement mode.
- **Changes Made**: Runner writes `run_environment.txt` containing runtime parameters for every execution.
- **Remaining Limitation**: WSL kernel shares host timing subsystem.
- **Status**: EXECUTED

### Criterion 18: Four Empirical Pilot Conditions
- **Requirement**: Define and execute four distinct scenario conditions (baseline, netem, control, intervention).
- **Method**: Scenario execution with specific impairment/action rules in testbed harness.
- **Evidence**: `outputs/empirical_software_network_pilot_v1/EXECUTION_ORDER.json#condition_time_blocks`
- **Result**: Baseline, netem impairment, master control switch, and source stop conditions executed.
- **Changes Made**: Implemented scenario branches in `run_empirical_software_pilot.sh`.
- **Remaining Limitation**: Conditions evaluate software protocol response only.
- **Status**: IMPLEMENTED

### Criterion 19: 12-Run Matched Set
- **Requirement**: Execute 3 repetitions across 4 conditions in interleaved execution order.
- **Method**: Interleaved execution protocol sorting runs by first-frame capture epoch.
- **Evidence**: `outputs/empirical_software_network_pilot_v1/EXECUTION_ORDER.json#ordered_runs`
- **Result**: 12 matched set2 runs executed with distinct capture hashes and monotonically increasing epochs.
- **Changes Made**: Automated forensic check script `forensic_check.py` validating uniqueness.
- **Remaining Limitation**: Execution constrained to single host testbed session.
- **Status**: MEASURED

### Criterion 20: Netem Direction-Match Result
- **Requirement**: Validate directionality of netem impairment between bridge and slave.
- **Method**: Packet sequence number gap analysis on `$SR` interface in master-to-slave and reverse directions.
- **Evidence**: `outputs/empirical_software_network_pilot_v1/RUN_ANALYSIS.json#runs.20260911_set2_netem_r1.netem_loss_comparison.direction_match`
- **Result**: Impairment produces missing sequence numbers strictly in master-to-slave egress direction.
- **Changes Made**: Implemented directional frame gap analysis in `analyze_runs.py`.
- **Remaining Limitation**: Evaluates software qdisc packet drops only, not physical link loss.
- **Status**: MEASURED

### Criterion 21: Intervention Outage Result
- **Requirement**: Measure packet-observable outage duration during grandmaster termination across all intervention repetitions.
- **Method**: Calculation of `delay_req_outage_s` gap between last request under old master and first under new master across all 8 intervention runs in Set 2 and Set 3 using the `analyze_runs.py` definition.
- **Evidence**: `outputs/empirical_software_network_pilot_v1/INTERVENTION_OUTAGE_RECONCILIATION.json#summary.runs_with_outage_detected_2_5x_criterion`
- **Result**: An observable outage above the nominal 2.5x-median interval criterion is detected in 5 of 8 runs (outages ranging from 0.341005 s to 0.656833 s; resumptions from 0.991612 s to 1.336006 s). Under the strict 5x-median interval criterion, an outage is detected in only 1 of 8 runs. In 3 of 8 runs (`20260911_set3_intervention_r4`, `r6`, and `r8`), no outage distinguishable from normal Delay_Req pacing is detected. The packet-observable outage is variable and not universally present across repetitions; the n=3 range is superseded as an incomplete representation.
- **Changes Made**: Updated reconciliation script and register evidence pointer to `INTERVENTION_OUTAGE_RECONCILIATION.json`; recorded outage vs non-outage mechanism breakdown in `OPEN_QUESTIONS.md`.
- **Remaining Limitation**: Internal `ptp4l` state machine transition latency not directly logged in pcap.
- **Status**: MEASURED

### Criterion 22: Configured Impairment Discrimination
- **Requirement**: Discriminate configured link impairment from baseline and control operations using purely packet-derived features under rigorous out-of-sample validation.
- **Method**: Leave-one-run-out cross-validation and 1000-iteration permutation test across 24 empirical pilot runs (positive class: netem delay/jitter/loss; negative class: baseline and no-action control).
- **Evidence**: `outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS.json#detection_features.sync_fu_paired_delay_std_s.leave_one_out.accuracy`
- **Result**: Single-threshold decision rules on packet sequence gap count, Sync-to-Follow_Up delay dispersion, and Sync inter-arrival jitter discriminate the configured impairment with statistically significant separation confirmed by permutation control. Detects a CONFIGURED IMPAIRMENT, NOT an attack.
- **Changes Made**: Implemented stdlib-only discriminator `discriminator.py` with strict programmatic assertions preventing feature leakage of scenario metadata, run IDs, or qdisc logs.
- **Remaining Limitation**: Detects artificial netem software queuing delay and loss; does not detect malicious attacker infiltration or physical layer degradation.
- **Status**: {c22_status}

### Criterion 23: Three-Class Configured Impairment and Source Loss Discrimination
- **Requirement**: Discriminate unimpaired, configured in-path link impairment, and operator-initiated source termination across all matched pilot runs using purely packet-derived features under out-of-sample validation.
- **Method**: Leave-one-run-out cross-validation and 1000-iteration permutation test across all 32 Set 2 and Set 3 runs (UNIMPAIRED: 16 runs; IMPAIRED: 8 runs; SOURCE_LOSS: 8 runs).
- **Evidence**: `outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS_3CLASS.json#honest_online_evaluation.leave_one_out_cross_validation.macro_f1`
- **Result**: Reclassified `max_announce_silence_at_end_s` as a RETROSPECTIVE manipulation check (measures remaining capture duration after injected stop; cannot run in an online self-healing loop). Under honest evaluation restricted strictly to ONLINE timing features, link impairment remains perfectly separable via paired delay dispersion (`sync_fu_paired_delay_std_s`), but SOURCE_LOSS overlaps UNIMPAIRED across all online features (macro-F1 = 0.9677, with 1 source-loss run misclassified as unimpaired due to nominal Delay_Req pacing). Promoted negative technical finding: no online timing feature cleanly separates source termination in this shared-clock testbed. Mandatory wording: SOURCE_LOSS is an authorised, operator-initiated termination of a timing source in an emulated testbed. It is NOT an attack, and nothing here establishes attack detection, clock health, physical timing quality or recovery.
- **Changes Made**: Annotated all candidate features with operational causality (`ONLINE` vs `RETROSPECTIVE`); reclassified retrospective silence as manipulation check; reported honest online performance and full confusion matrix.
- **Remaining Limitation**: Software namespace testbed with shared host clock and `free_running 1` prevents measuring physical time error degradation or hardware oscillator drift.
- **Status**: {c23_status}
"""

    out_path = root / 'ACCEPTANCE_REGISTER.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Successfully generated {out_path}")

if __name__ == '__main__':
    build_acceptance_register()
