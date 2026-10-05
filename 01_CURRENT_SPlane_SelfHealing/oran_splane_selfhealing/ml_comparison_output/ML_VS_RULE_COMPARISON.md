# AI-native vs frozen rule-based timing classification

## Outcome

This pre-registered comparison completed on the held-out replicate sessions 9-12. The input SHA-256 matched `bc20005f270e2679d4d0f656600ce07e6c7ff8ed9d8ca98f4c1a07477414b1c7`. The archive contained exactly 168 runs. It did not fully meet the stated file inventory: 48 files were missing, all of them `pmc.jsonl`.

ARM A was read only from `decision_v3.json`. ARM B used the shipped Random Forest family with 90 trees, depth 6, balanced class weights, and seed 1588. The generic repository helper was not called because it randomly splits windows; this harness applied the required session-disjoint split first (train reps 1-8, test reps 9-12), then fitted the identical estimator. Hyperparameters, split, features, novelty settings, and aggregation were fixed before head-to-head scoring.

The final ARM B verdict uses the configured group Isolation Forest as an abstention layer: novel windows become `UNKNOWN`; other windows retain the RF `H0`/`H1` result. A run receives a verdict only when one window verdict has a strict majority; otherwise it is `UNKNOWN`.

The constant always-BENIGN control scores 20/56 (0.357), versus ARM B's 24/56 (0.429). ARM B itself returns `BENIGN` on 47/56 runs (83.9%). The paired gain is only four net runs: ARM B is correct while the baseline is wrong on 5 runs, and the baseline is correct while ARM B is wrong on 1 run. The exact two-sided McNemar p-value is 0.21875; therefore ARM B is **not distinguishable from the constant-BENIGN predictor at alpha 0.05** on this sample.

## Feature availability

Populated and used (6): `offset_mean`, `offset_std`, `offset_abs_max`, `path_delay_mean`, `pdv_std`, `holdover_rate`.

Entirely empty and excluded (22): `seq_regressions`, `msg_irregularity`, `synce_ql_max`, `gnss_loss_rate`, `msg_rate_mean`, `msg_rate_std`, `gm_identity_changes`, `gm_identity_churn`, `clock_class_changes`, `clock_class_improve_jump`, `priority1_changes`, `steps_removed_changes`, `steps_removed_min`, `gnss_status_changes`, `antenna_fault_rate`, `satellites_drop_max`, `satellites_mean`, `holdover_entry_count`, `drift_vs_declared_state_residual`, `holdover_spec_violation_rate`, `status_behaviour_disagreement`, `offset_step_vs_drift_ratio`.

The exclusion is provenance-based. The existing canonical ingester fills simulator-friendly defaults and creates synthetic sequence/message fields so downstream code can run. Those are not measurements in these logs, so this experiment reset their derived feature columns to NaN before fitting. No unavailable value was changed to zero or otherwise imputed.

## Primary per-scenario results

Each cell covers four held-out runs. CIs are Wilson 95% intervals for exact expected-verdict correctness. This table, not pooled window counts, is primary.

| Scenario | Expected | ARM A verdicts | ARM B verdicts | Always-BENIGN correct/n | ARM A correct/n (95% CI) | ARM B correct/n (95% CI) |
|---|---|---|---|---:|---:|---:|
| A1_rogue_master | ATTACK | ATTACKx4 | BENIGNx4 | 0/4 | 4/4 (0.510-1.000) | 0/4 (0.000-0.490) |
| A2_sync_spoof | ATTACK | ATTACKx4 | BENIGNx4 | 0/4 | 4/4 (0.510-1.000) | 0/4 (0.000-0.490) |
| A3_replay | ATTACK | ATTACKx4 | ATTACKx1, UNKNOWNx3 | 0/4 | 4/4 (0.510-1.000) | 1/4 (0.046-0.699) |
| A5_dos_flood | ATTACK | ATTACKx4 | ATTACKx1, BENIGNx3 | 0/4 | 4/4 (0.510-1.000) | 1/4 (0.046-0.699) |
| A8_rogue_bc | ATTACK | ATTACKx4 | ATTACKx1, BENIGNx3 | 0/4 | 4/4 (0.510-1.000) | 1/4 (0.046-0.699) |
| C1_removal | ATTACK | ATTACKx3, BENIGNx1 | BENIGNx4 | 0/4 | 3/4 (0.301-0.954) | 0/4 (0.000-0.490) |
| C2_malformed | ATTACK | ATTACKx4 | ATTACKx1, BENIGNx3 | 0/4 | 4/4 (0.510-1.000) | 1/4 (0.046-0.699) |
| C3_wholesecond | ATTACK | ATTACKx4 | ATTACKx1, BENIGNx3 | 0/4 | 4/4 (0.510-1.000) | 1/4 (0.046-0.699) |
| baseline | BENIGN | BENIGNx4 | BENIGNx4 | 4/4 | 4/4 (0.510-1.000) | 4/4 (0.510-1.000) |
| B2_gm_failover | BENIGN | BENIGNx4 | BENIGNx4 | 4/4 | 4/4 (0.510-1.000) | 4/4 (0.510-1.000) |
| B3_pdv_congestion | BENIGN | BENIGNx4 | ATTACKx1, BENIGNx3 | 4/4 | 4/4 (0.510-1.000) | 3/4 (0.301-0.954) |
| B7_topology_change | BENIGN | BENIGNx4 | BENIGNx4 | 4/4 | 4/4 (0.510-1.000) | 4/4 (0.510-1.000) |
| B_bc_replacement | BENIGN | ATTACKx4 | BENIGNx4 | 4/4 | 0/4 (0.000-0.490) | 4/4 (0.510-1.000) |
| B_unplanned_failover | UNKNOWN | UNKNOWNx4 | BENIGNx4 | 0/4 | 4/4 (0.510-1.000) | 0/4 (0.000-0.490) |

## Macro results

- Attack-scenario sensitivity: ARM A 0.969; ARM B 0.156.
- Benign-scenario specificity: ARM A 0.800; ARM B 0.950.
- `B_unplanned_failover` abstention correctness: ARM A 1.000; ARM B 0.000.

The JSON also reports pooled Wilson intervals, explicitly labelled run-count-dependent. Overlapping-window metrics are secondary because those windows are correlated.

## Evidence-backed answers

### a) Which arm wins on which fault classes, and by how much?

- `A1_rogue_master`: ARM A by 100 percentage points.
- `A2_sync_spoof`: ARM A by 100 percentage points.
- `A3_replay`: ARM A by 75 percentage points.
- `A5_dos_flood`: ARM A by 75 percentage points.
- `A8_rogue_bc`: ARM A by 75 percentage points.
- `C1_removal`: ARM A by 75 percentage points.
- `C2_malformed`: ARM A by 75 percentage points.
- `C3_wholesecond`: ARM A by 75 percentage points.
- `baseline`: tie.
- `B2_gm_failover`: tie.
- `B3_pdv_congestion`: ARM A by 25 percentage points.
- `B7_topology_change`: tie.
- `B_bc_replacement`: ARM B by 100 percentage points.
- `B_unplanned_failover`: ARM A by 100 percentage points.

### b) Crossovers

The raw ARM-B-correct/ARM-A-wrong crossover is `B_bc_replacement`. This is **not a unique ARM B capability**: ARM B and the always-BENIGN control both score 4/4 because both simply return `BENIGN` on those runs. Across all held-out runs, ARM B improves on the trivial control by only 4/56 net runs, and the paired exact test does not distinguish them (p=0.21875).

Scenarios where ARM A was correct on at least one run that ARM B missed: `A1_rogue_master`, `A2_sync_spoof`, `A3_replay`, `A5_dos_flood`, `A8_rogue_bc`, `B3_pdv_congestion`, `B_unplanned_failover`, `C1_removal`, `C2_malformed`, `C3_wholesecond`.

### c) Measured combinations

- Single-arm reference: ARM A exact accuracy 0.911 (51/56); ARM B 0.429 (24/56); always-BENIGN 0.357 (20/56).
- OR (ATTACK if either attacks): sensitivity 0.969, specificity 0.750, abstention correctness 1.000, exact accuracy 0.893.
- Rule-first, ML only on rule abstention: sensitivity 0.969, specificity 0.800, abstention correctness 0.000, exact accuracy 0.839.
- Consensus, otherwise abstain: sensitivity 0.156, specificity 0.750, abstention correctness 1.000, exact accuracy 0.429.

None of the three measured combinations beats ARM A's exact accuracy. OR is closest but loses specificity on benign cases; rule-first destroys correct abstention by replacing ARM A's `UNKNOWN` with ARM B's over-confident benign call. No unmeasured combination is recommended.

### d) Domain shift / artefact evidence

ARM B's ranked impurity importances are: `offset_abs_max` (0.268), `path_delay_mean` (0.262), `offset_std` (0.208), `pdv_std` (0.139), `offset_mean` (0.124), `holdover_rate` (0.000). It can key only on offset, path-delay variability, and servo-state holdover because all protocol-legality, BMCA, GNSS, SyncE, message-rate, and oscillator-consistency features are unavailable. The weak held-out window accuracy (0.544), ROC-AUC (0.604), and attack-scenario sensitivity (0.156) are signs of poor transfer across randomized replicate sessions and/or non-identifiability from servo summaries alone. Strong importance on timing magnitude/dispersion shows the classifier is learning this testbed's servo signatures, not the protocol illegality or operator-context semantics that define several attacks. That establishes artefact risk, but one testbed cannot separate domain shift from intrinsic class overlap. Transfer to another topology, hardware clock, reporting cadence, or site is NOT ESTABLISHED.

## Measured, calculated, and assumed

- Measured: checksum, file inventory, parser outcomes, feature values, frozen ARM A verdicts, ARM B predictions, and feature importances.
- Calculated: window/run aggregation, correctness, macro rates, confusion matrices, and Wilson intervals.
- Assumed before scoring: node-local timestamp rebasing and within-run pooling; novelty means abstention; strict majority produces the run verdict.

## Limitations

- Forty-eight of 168 run directories lack pmc.jsonl; management-plane telemetry is therefore incomplete and was not used as an ML feature source.
- 36 context.json files disagree with their directory replicate number (the C-series files report rep 901). The pre-registered split uses the authoritative <scenario>__r<rep> directory name.
- The gma.log and gmb.log files contain no parseable servo lines because those nodes act as grandmasters; this produced 336 preserved parser failures. BC/RU logs supplied the usable servo telemetry.
- The canonical ingester supplies simulator-friendly defaults and synthetic sequence/message fields. Values derived only from those defaults were explicitly reset to NaN and excluded from ARM B.
- The 0.4 s window is shorter than the roughly 2 s servo reporting cadence. A usable window is formed by pooling contemporaneous BC/RU samples after each node-local timestamp is rebased; it is cross-node rather than a dense single-node time window.
- Window labels inherit the run-level scenario label, so pre-fault/settling windows may contain label noise.
- Overlapping windows are correlated. Per-run, per-scenario results are primary; pooled window metrics have artificially large effective sample size.
- Only four held-out replicates exist per scenario, giving wide Wilson intervals.
- ARM A consumes protocol legality and provisioned context, whereas ARM B here is restricted to available ptp4l servo summaries. This is a head-to-head operational comparison, not an equal-input ablation.
- The experiment uses one fixed split and one fixed seed as pre-registered; it does not estimate split-to-split or seed-to-seed variance.
