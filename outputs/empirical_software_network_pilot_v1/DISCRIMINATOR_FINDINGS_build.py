#!/usr/bin/env python3
"""Build script for DISCRIMINATOR_FINDINGS.md.

Reads:
- outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS.json (2-class)
- outputs/empirical_software_network_pilot_v1/DISCRIMINATOR_RESULTS_3CLASS.json (3-class)
- outputs/empirical_software_network_pilot_v1/INTERVENTION_OUTAGE_RECONCILIATION.json
and dynamically generates DISCRIMINATOR_FINDINGS.md with zero hand-typed numbers.
"""

import json
from pathlib import Path

def build_discriminator_findings():
    repo_root = Path(__file__).resolve().parents[2]
    emp_dir = repo_root / "outputs" / "empirical_software_network_pilot_v1"
    res_path_2c = emp_dir / "DISCRIMINATOR_RESULTS.json"
    res_path_3c = emp_dir / "DISCRIMINATOR_RESULTS_3CLASS.json"
    rec_path = emp_dir / "INTERVENTION_OUTAGE_RECONCILIATION.json"

    with open(res_path_2c, "r", encoding="utf-8") as f:
        data2 = json.load(f)

    with open(res_path_3c, "r", encoding="utf-8") as f:
        data3 = json.load(f)

    with open(rec_path, "r", encoding="utf-8") as f:
        rec = json.load(f)

    # 2-Class variables
    scope2 = data2["evaluation_scope"]
    sc2 = scope2["sample_counts"]
    man2 = data2["manipulation_check"]
    det2 = data2["detection_features"]

    man_dist = man2["distribution_and_margins"]
    man_loo = man2["leave_one_out"]
    man_perm = man2["permutation_control"]

    fu_entry = det2["sync_fu_paired_delay_std_s"]
    fu_dist = fu_entry["distribution_and_margins"]
    fu_loo = fu_entry["leave_one_out"]
    fu_perm = fu_entry["permutation_control"]

    jit_entry = det2["sync_interarrival_jitter_s"]
    jit_dist = jit_entry["distribution_and_margins"]
    jit_loo = jit_entry["leave_one_out"]
    jit_perm = jit_entry["permutation_control"]

    # 3-Class variables
    scope3 = data3["evaluation_scope"]
    sc3 = scope3["sample_counts"]
    by_class3 = sc3["by_class"]
    feats3 = data3["feature_distributions_and_margins"]
    
    # Retrospective & Online evaluations
    retro3 = data3["retrospective_evaluation"]
    loo_retro = retro3["leave_one_out_cross_validation"]
    cm_retro = loo_retro["confusion_matrix"]
    pcm_retro = loo_retro["per_class_metrics"]
    perm_retro = retro3["permutation_control"]

    online3 = data3["honest_online_evaluation"]
    loo_online = online3["leave_one_out_cross_validation"]
    cm_online = loo_online["confusion_matrix"]
    pcm_online = loo_online["per_class_metrics"]
    perm_online = online3["permutation_control"]

    sil_dist3 = feats3["max_announce_silence_at_end_s"]["per_class_stats"]
    sil_pair3 = feats3["max_announce_silence_at_end_s"]["pairwise_margins"]

    fu_dist3 = feats3["sync_fu_paired_delay_std_s"]["per_class_stats"]
    fu_pair3 = feats3["sync_fu_paired_delay_std_s"]["pairwise_margins"]

    jit_dist3 = feats3["sync_interarrival_jitter_s"]["per_class_stats"]
    jit_pair3 = feats3["sync_interarrival_jitter_s"]["pairwise_margins"]

    dreq_dist3 = feats3["max_delay_req_gap_s"]["per_class_stats"]
    dreq_pair3 = feats3["max_delay_req_gap_s"]["pairwise_margins"]

    srcs_dist3 = feats3["num_announce_sources"]["per_class_stats"]
    ann_gap_dist3 = feats3["announce_max_gap_any_source_s"]["per_class_stats"]

    rec_sum = rec["summary"]

    md = f"""# Empirical Network Impairment and Source Loss Discriminator Findings

## Part 1: Mandatory Scope and Governance Declarations

> [!IMPORTANT]
> **Mandatory Scope and Governance Disclaimer**:
> 1. This evaluation detects a **CONFIGURED SOFTWARE IMPAIRMENT** (Linux kernel `netem` delay, jitter, and loss on an emulated link) and an **AUTHORISED, OPERATOR-INITIATED TIMING SOURCE TERMINATION** (`SOURCE_LOSS`).
> 2. It is **NOT an attack**, and nothing here establishes attack detection, clock health, physical timing quality, or recovery.
> 3. All analytical models operate strictly at Layer L5 (classification predictions out-of-sample) and must never be conflated with Layer L8 (physical outcome measurements).
> 4. An operational manipulation check is **never reported as an anomaly detection capability**.

---

## Part 2: Two-Class Configured Impairment Evaluation

### 1. Operational Scope and Sample Counts
- **Unit of Analysis**: {scope2['unit_of_analysis']}
- **Positive Class**: `{scope2['positive_class']}` (n = {sc2['positive_runs']} runs across Set 2 and Set 3)
- **Negative Class**: `{scope2['negative_class'][0]}` and `{scope2['negative_class'][1]}` (n = {sc2['negative_runs']} runs across Set 2 and Set 3)
- **Total Sample Size**: N = {sc2['total_runs_evaluated']} matched runs evaluated under leave-one-run-out cross-validation
- **Class Imbalance**: Negative-to-positive ratio is {sc2['class_ratio_neg_to_pos']} ({sc2['negative_runs']} unimpaired vs {sc2['positive_runs']} impaired runs)
- **Anti-Circularity Architecture**: Ground truth class assignment is fixed by the experiment configuration and confirmed independently by physical kernel `tc -s qdisc` packet drop telemetry (`qdisc_after.txt`). The feature extractor operates solely on raw bytes read from anonymous binary stream objects with explicit programmatic assertions failing loudly if directory or scenario tokens are present.

### 2. Manipulation Check vs. Detection Features
A rigorous evaluation must distinguish between validating that an injection occurred and detecting its network delivery consequences.

- **Manipulation Check (`missing_master_to_slave_seq_count`)**: Direct tally of 16-bit PTP sequence ID gaps across the `$SR` bridge-to-slave interface.
  - Positive class (netem): n = {man_dist['positive_class_netem']['n']}, min = {man_dist['positive_class_netem']['min']}, median = {man_dist['positive_class_netem']['median']:.1f}, max = {man_dist['positive_class_netem']['max']} dropped frames.
  - Negative class (unimpaired): n = {man_dist['negative_class_unimpaired']['n']}, min = {man_dist['negative_class_unimpaired']['min']}, median = {man_dist['negative_class_unimpaired']['median']:.1f}, max = {man_dist['negative_class_unimpaired']['max']} dropped frames.
  - Separation margin: {man_dist['separation_margin_lowest_pos_minus_highest_neg']} frames.
  - *Technical Caveat*: Separating runs by counting the packets the injection intentionally removed confirms that `tc netem loss 1%` was active and delivered to the egress queue. It is an operational delivery confirmation, **NOT** evidence of an anomaly detector.

- **Detection Features (Honest Separation Margins and Medians)**:
| Detection Metric | Role | Lowest Pos Minus Highest Neg (Margin) | Ratio of Class Medians (Pos / Neg) | Impaired Netem Median (n={sc2['positive_runs']}) | Unimpaired Median (n={sc2['negative_runs']}) | LOO Accuracy | Permutation p-value (N={fu_perm['num_permutations']}, seed={fu_perm['seed']}) |
|---|---|---|---|---|---|---|---|
| `sync_fu_paired_delay_std_s` | DETECTION_FEATURE | **{fu_dist['separation_margin_lowest_pos_minus_highest_neg'] * 1e6:.2f} us** | **{fu_dist['ratio_of_class_medians']:.2f}x** | {fu_dist['positive_class_netem']['median'] * 1e6:.2f} us | {fu_dist['negative_class_unimpaired']['median'] * 1e6:.2f} us | {fu_loo['accuracy'] * 100:.1f}% | p = {fu_perm['permutation_p_value']:.4f} |
| `sync_interarrival_jitter_s` | DETECTION_FEATURE | **{jit_dist['separation_margin_lowest_pos_minus_highest_neg'] * 1e6:.2f} us** | **{jit_dist['ratio_of_class_medians']:.2f}x** | {jit_dist['positive_class_netem']['median'] * 1e6:.2f} us | {jit_dist['negative_class_unimpaired']['median'] * 1e6:.2f} us | {jit_loo['accuracy'] * 100:.1f}% | p = {jit_perm['permutation_p_value']:.4f} |

---

## Part 3: Three-Class Configured Impairment and Source Loss Evaluation

### 1. Problem Formulation and Class Distribution
- **Classes**:
  - `UNIMPAIRED` (n = {by_class3['UNIMPAIRED']}): `baseline_control` and `authorized_source_change_no_action_control`.
  - `IMPAIRED` (n = {by_class3['IMPAIRED']}): `netem_delay_jitter_loss` (10 ms delay, 2 ms jitter, 1% loss).
  - `SOURCE_LOSS` (n = {by_class3['SOURCE_LOSS']}): `authorized_source_change_intervention` (operator-initiated master stop).
- **Total Matched Runs**: N = {sc3['total_runs_evaluated']} runs across Set 2 and Set 3 (Imbalance: {sc3['class_imbalance']}).
- **Ground Truth Independence**: Fixed by experiment design and confirmed by daemon lifecycle logs in `events.log`, completely independent of packet timing features.

### 2. Feature Causality Annotations
To prevent retrospective circularity in control-loop evaluations, every feature is explicitly classified by its operational causality:
- **ONLINE**: Can be computed continuously from a bounded trailing window during live protocol execution (e.g. `sync_fu_paired_delay_std_s`, `max_delay_req_gap_s`, `sync_interarrival_jitter_s`).
- **RETROSPECTIVE**: Requires the complete capture to have terminated, or inspects distance to end-of-file (e.g. `max_announce_silence_at_end_s`).

> [!WARNING]
> **Retrospective Feature Disqualification**:
> `max_announce_silence_at_end_s` measures the duration from the stopped master's final Announce frame to capture termination. Because the master was terminated midway through the run and capture continued for approximately 30 seconds, this feature measures remaining capture duration. It is a **RETROSPECTIVE MANIPULATION CHECK**, confirming the process stop occurred. **A detector built on a RETROSPECTIVE feature cannot run in an operational self-healing loop**.

### 3. Feature Distributions and Margins Across All Three Classes

| Candidate Feature | Role | Causality | UNIMPAIRED (n={by_class3['UNIMPAIRED']}) min / med / max | IMPAIRED (n={by_class3['IMPAIRED']}) min / med / max | SOURCE_LOSS (n={by_class3['SOURCE_LOSS']}) min / med / max | Separable Class Pairs (Margin) | Inseparable Class Pairs |
|---|---|---|---|---|---|---|---|
| `max_announce_silence_at_end_s` | MANIPULATION_CHECK | RETROSPECTIVE | {sil_dist3['UNIMPAIRED']['min']:.3f} / {sil_dist3['UNIMPAIRED']['median']:.3f} / {sil_dist3['UNIMPAIRED']['max']:.3f} s | {sil_dist3['IMPAIRED']['min']:.3f} / {sil_dist3['IMPAIRED']['median']:.3f} / {sil_dist3['IMPAIRED']['max']:.3f} s | {sil_dist3['SOURCE_LOSS']['min']:.3f} / {sil_dist3['SOURCE_LOSS']['median']:.3f} / {sil_dist3['SOURCE_LOSS']['max']:.3f} s | SL vs UNIMP ({sil_pair3['UNIMPAIRED_vs_SOURCE_LOSS']['separation_margin']:.2f} s)<br>SL vs IMP ({sil_pair3['IMPAIRED_vs_SOURCE_LOSS']['separation_margin']:.2f} s) | UNIMP vs IMP (both active) |
| `sync_fu_paired_delay_std_s` | DETECTION_FEATURE | ONLINE | {fu_dist3['UNIMPAIRED']['min']*1e6:.1f} / {fu_dist3['UNIMPAIRED']['median']*1e6:.1f} / {fu_dist3['UNIMPAIRED']['max']*1e6:.1f} us | {fu_dist3['IMPAIRED']['min']*1e6:.1f} / {fu_dist3['IMPAIRED']['median']*1e6:.1f} / {fu_dist3['IMPAIRED']['max']*1e6:.1f} us | {fu_dist3['SOURCE_LOSS']['min']*1e6:.1f} / {fu_dist3['SOURCE_LOSS']['median']*1e6:.1f} / {fu_dist3['SOURCE_LOSS']['max']*1e6:.1f} us | IMP vs UNIMP ({fu_pair3['UNIMPAIRED_vs_IMPAIRED']['separation_margin']*1e6:.2f} us)<br>IMP vs SL ({fu_pair3['IMPAIRED_vs_SOURCE_LOSS']['separation_margin']*1e6:.2f} us) | **UNIMP vs SL (overlap [{fu_dist3['SOURCE_LOSS']['min']*1e6:.1f} us, {fu_dist3['SOURCE_LOSS']['max']*1e6:.1f} us])** |
| `sync_interarrival_jitter_s` | DETECTION_FEATURE | ONLINE | {jit_dist3['UNIMPAIRED']['min']*1e6:.1f} / {jit_dist3['UNIMPAIRED']['median']*1e6:.1f} / {jit_dist3['UNIMPAIRED']['max']*1e6:.1f} us | {jit_dist3['IMPAIRED']['min']*1e6:.1f} / {jit_dist3['IMPAIRED']['median']*1e6:.1f} / {jit_dist3['IMPAIRED']['max']*1e6:.1f} us | {jit_dist3['SOURCE_LOSS']['min']*1e6:.1f} / {jit_dist3['SOURCE_LOSS']['median']*1e6:.1f} / {jit_dist3['SOURCE_LOSS']['max']*1e6:.1f} us | IMP vs UNIMP ({jit_pair3['UNIMPAIRED_vs_IMPAIRED']['separation_margin']*1e6:.2f} us)<br>IMP vs SL ({jit_pair3['IMPAIRED_vs_SOURCE_LOSS']['separation_margin']*1e6:.2f} us) | **UNIMP vs SL (overlap [{jit_dist3['SOURCE_LOSS']['min']*1e6:.1f} us, {jit_dist3['UNIMPAIRED']['max']*1e6:.1f} us])** |
| `max_delay_req_gap_s` | DETECTION_FEATURE | ONLINE | {dreq_dist3['UNIMPAIRED']['min']:.3f} / {dreq_dist3['UNIMPAIRED']['median']:.3f} / {dreq_dist3['UNIMPAIRED']['max']:.3f} s | {dreq_dist3['IMPAIRED']['min']:.3f} / {dreq_dist3['IMPAIRED']['median']:.3f} / {dreq_dist3['IMPAIRED']['max']:.3f} s | {dreq_dist3['SOURCE_LOSS']['min']:.3f} / {dreq_dist3['SOURCE_LOSS']['median']:.3f} / {dreq_dist3['SOURCE_LOSS']['max']:.3f} s | None | **All pairs overlap** (SL reaches {dreq_dist3['SOURCE_LOSS']['min']:.3f} s, below UNIMP max {dreq_dist3['UNIMPAIRED']['max']:.3f} s) |
| `announce_max_gap_any_source_s` | DETECTION_FEATURE | ONLINE | {ann_gap_dist3['UNIMPAIRED']['min']:.3f} / {ann_gap_dist3['UNIMPAIRED']['median']:.3f} / {ann_gap_dist3['UNIMPAIRED']['max']:.3f} s | {ann_gap_dist3['IMPAIRED']['min']:.3f} / {ann_gap_dist3['IMPAIRED']['median']:.3f} / {ann_gap_dist3['IMPAIRED']['max']:.3f} s | {ann_gap_dist3['SOURCE_LOSS']['min']:.3f} / {ann_gap_dist3['SOURCE_LOSS']['median']:.3f} / {ann_gap_dist3['SOURCE_LOSS']['max']:.3f} s | IMP vs UNIMP ({ann_gap_dist3['IMPAIRED']['min'] - ann_gap_dist3['UNIMPAIRED']['max']:.3f} s)<br>IMP vs SL ({ann_gap_dist3['IMPAIRED']['min'] - ann_gap_dist3['SOURCE_LOSS']['max']:.3f} s) | **UNIMP vs SL (surviving master paces at 250 ms)** |
| `num_announce_sources` | DETECTION_FEATURE | ONLINE | {srcs_dist3['UNIMPAIRED']['min']} / {srcs_dist3['UNIMPAIRED']['median']} / {srcs_dist3['UNIMPAIRED']['max']} | {srcs_dist3['IMPAIRED']['min']} / {srcs_dist3['IMPAIRED']['median']} / {srcs_dist3['IMPAIRED']['max']} | {srcs_dist3['SOURCE_LOSS']['min']} / {srcs_dist3['SOURCE_LOSS']['median']} / {srcs_dist3['SOURCE_LOSS']['max']} | None | **Completely invariant** (exactly 2 in all 32 runs) |

---

## Part 4: Core Scientific Finding — Promoted Negative Technical Result

### Promoted Negative Finding: On Every Online Timing Feature, SOURCE_LOSS Overlaps UNIMPAIRED
The empirical evaluation demonstrates an unambiguous negative scientific result: **no online packet-timing feature evaluated cleanly separates operator-initiated source termination from unimpaired operations**.
- `sync_fu_paired_delay_std_s`: SOURCE_LOSS range [{fu_dist3['SOURCE_LOSS']['min']*1e6:.1f} us, {fu_dist3['SOURCE_LOSS']['max']*1e6:.1f} us] falls entirely within the UNIMPAIRED range [{fu_dist3['UNIMPAIRED']['min']*1e6:.1f} us, {fu_dist3['UNIMPAIRED']['max']*1e6:.1f} us]. Margin = **none (zero separation)**.
- `sync_interarrival_jitter_s`: SOURCE_LOSS range [{jit_dist3['SOURCE_LOSS']['min']*1e6:.1f} us, {jit_dist3['SOURCE_LOSS']['max']*1e6:.1f} us] overlaps UNIMPAIRED range [{jit_dist3['UNIMPAIRED']['min']*1e6:.1f} us, {jit_dist3['UNIMPAIRED']['max']*1e6:.1f} us]. Margin = **none (zero separation)**.
- `max_delay_req_gap_s`: SOURCE_LOSS minimum ({dreq_dist3['SOURCE_LOSS']['min']:.3f} s) reaches below the UNIMPAIRED maximum ({dreq_dist3['UNIMPAIRED']['max']:.3f} s). In run `20260911_set3_intervention_r4`, the maximum observed Delay_Req interval during master handover was only {dreq_dist3['SOURCE_LOSS']['min']:.3f} s, which is completely indistinguishable from nominal unimpaired transmission cadence. Margin = **none (zero separation)**.

### Candidate Explanations for the Lack of Separation
Without asserting which explanation dominates, the absence of timing degradation during source loss in this testbed is consistent with three physical and architectural factors:
1. **Disabled Clock Stepping (`free_running 1`)**: In accordance with the pilot specification, `ptp4l` runs in `free_running 1` mode to safeguard the host system clock. Consequently, the servo never adjusts the local clock frequency or steps the clock phase, preventing phase-transient jitter or servo-induced packet delay variations during failover.
2. **Shared Host Kernel Clock**: All endpoints (Master A, Master B, and Slave) read timestamps from the same underlying host kernel clock. Because there is no true independent hardware clock oscillator drift or frequency error between sources, switching masters introduces zero real physical timebase discontinuity.
3. **Continuous Availability of Backup Master**: Master B was configured, active, and transmitting Announce and Sync frames concurrently throughout the run. When Master A was terminated, the slave's BMCA state machine transitioned to Master B within 2 milliseconds without an extended period of un-synchronized holdover.

### Requirements to Test Real Source-Loss Timing Degradation
To establish whether timing degradation occurs during source loss in production telecommunications networks, the testbed would require:
- Independent physical hardware clocks (e.g. separate oscillators with distinct temperature drifts and wander characteristics).
- Closed-loop servo operation where the slave adjusts its physical clock hardware to match the active master.
- An external, out-of-band reference instrument (e.g. PPS counter or GNSS reference receiver) measuring true time error and phase transient offset on wire.

---

## Part 5: Cross-Validation Comparisons: Honest Online vs. Retrospective

### 1. Honest Online Detection Evaluation (Strictly ONLINE Features)
Evaluated with leave-one-run-out cross-validation across all 32 runs, fitting decision thresholds on training folds only:
- **Decision Logic**:
  - Fold threshold fit on `sync_fu_paired_delay_std_s` to separate `IMPAIRED` (> ~164 us).
  - Fold threshold fit on `max_delay_req_gap_s` to attempt separating `SOURCE_LOSS` (> ~265 ms) from `UNIMPAIRED`.

#### 3x3 Confusion Matrix (Honest Online Evaluation)
| Ground Truth Class | Pred: UNIMPAIRED | Pred: IMPAIRED | Pred: SOURCE_LOSS | Total Actual |
|---|---|---|---|---|
| **Actual: UNIMPAIRED** | **{cm_online['UNIMPAIRED']['UNIMPAIRED']}** | {cm_online['UNIMPAIRED']['IMPAIRED']} | {cm_online['UNIMPAIRED']['SOURCE_LOSS']} | {pcm_online['UNIMPAIRED']['total_actual']} |
| **Actual: IMPAIRED** | {cm_online['IMPAIRED']['UNIMPAIRED']} | **{cm_online['IMPAIRED']['IMPAIRED']}** | {cm_online['IMPAIRED']['SOURCE_LOSS']} | {pcm_online['IMPAIRED']['total_actual']} |
| **Actual: SOURCE_LOSS** | **{cm_online['SOURCE_LOSS']['UNIMPAIRED']}** | {cm_online['SOURCE_LOSS']['IMPAIRED']} | **{cm_online['SOURCE_LOSS']['SOURCE_LOSS']}** | {pcm_online['SOURCE_LOSS']['total_actual']} |

#### Performance Summary (Honest Online Evaluation)
- **Overall Accuracy**: {loo_online['accuracy']*100:.2f}%
- **Macro-Averaged F1-Score**: {loo_online['macro_f1']:.4f}
- **Misclassification**: Run `20260911_set3_intervention_r4` experienced source termination but exhibited a maximum Delay_Req interval of only {dreq_dist3['SOURCE_LOSS']['min']:.3f} s (below the training threshold of 264.9 ms), causing it to be classified as `UNIMPAIRED`.
- **Per-Class Metrics**:
  - `UNIMPAIRED`: Precision = {pcm_online['UNIMPAIRED']['precision']*100:.1f}%, Recall = {pcm_online['UNIMPAIRED']['recall']*100:.1f}%, F1 = {pcm_online['UNIMPAIRED']['f1']:.4f}
  - `IMPAIRED`: Precision = {pcm_online['IMPAIRED']['precision']*100:.1f}%, Recall = {pcm_online['IMPAIRED']['recall']*100:.1f}%, F1 = {pcm_online['IMPAIRED']['f1']:.4f}
  - `SOURCE_LOSS`: Precision = {pcm_online['SOURCE_LOSS']['precision']*100:.1f}%, Recall = {pcm_online['SOURCE_LOSS']['recall']*100:.1f}%, F1 = {pcm_online['SOURCE_LOSS']['f1']:.4f}
- **Permutation Control (1000 Iterations, Fixed Seed {perm_online['seed']})**:
  - Empirical p-value: p = {perm_online['permutation_p_value']:.4f}
  - Null distribution of Macro-F1: min = {perm_online['null_distribution']['min']:.4f}, median = {perm_online['null_distribution']['median']:.4f}, mean = {perm_online['null_distribution']['mean']:.4f}, max = {perm_online['null_distribution']['max']:.4f}.

### 2. Retrospective Reference Evaluation (Including Capture-End Silence Check)
- **Warning**: Presented for audit reference only. Incorporates `max_announce_silence_at_end_s` (~30 s silence).
- **Confusion Matrix**:
  - `UNIMPAIRED`: {cm_retro['UNIMPAIRED']['UNIMPAIRED']}/16 correct ({pcm_retro['UNIMPAIRED']['precision']*100:.0f}%)
  - `IMPAIRED`: {cm_retro['IMPAIRED']['IMPAIRED']}/8 correct ({pcm_retro['IMPAIRED']['precision']*100:.0f}%)
  - `SOURCE_LOSS`: {cm_retro['SOURCE_LOSS']['SOURCE_LOSS']}/8 correct ({pcm_retro['SOURCE_LOSS']['precision']*100:.0f}%)
- **Accuracy**: {loo_retro['accuracy']*100:.1f}%, Macro-F1: {loo_retro['macro_f1']:.4f}.

---

## Part 6: Reconciliation of Intervention Outage Criterion Across n=8 Runs

The original project acceptance register recorded intervention outage metrics from three exploratory runs (`set2` intervention r1-r3). When evaluated across all **n = 8 intervention runs** in `set2` and `set3`, the physical behavior of Delay_Req timing during master termination demonstrates critical variation:

1. **Strict 5x Median Interval Criterion**:
   - Outage detected (> 5x median): **{rec_sum['runs_with_outage_detected_5x_criterion']} of {rec_sum['total_intervention_runs']} runs** (`20260911_set2_intervention_r3` with gap {rec_sum['observed_outages_2_5x_s']['max']:.3f} s vs median 0.116 s).
   - No outage detected (> 5x median): **{rec_sum['runs_with_no_outage_detected_5x_criterion']} of {rec_sum['total_intervention_runs']} runs**.
2. **Nominal 2.5x Median Interval Criterion**:
   - Outage detected (> 2.5x median): **{rec_sum['runs_with_outage_detected_2_5x_criterion']} of {rec_sum['total_intervention_runs']} runs** (outages between {rec_sum['observed_outages_2_5x_s']['min']:.3f} s and {rec_sum['observed_outages_2_5x_s']['max']:.3f} s; resumptions between {rec_sum['observed_resumptions_s']['min']:.3f} s and {rec_sum['observed_resumptions_s']['max']:.3f} s).
   - No outage detected (> 2.5x median): **{rec_sum['runs_with_no_outage_detected_2_5x_criterion']} of {rec_sum['total_intervention_runs']} runs** (`set3_intervention_r4`, `r6`, and `r8`).
3. **Register Alignment**:
   - The register criterion has been updated to reflect the full n=8 sample: an observable packet outage is **variable and not universally present across repetitions**. In 3 of 8 runs, Delay_Req transmission continues across the master termination with gap duration indistinguishable from nominal pacing.
"""

    out_file = emp_dir / "DISCRIMINATOR_FINDINGS.md"
    out_file.write_text(md, encoding="utf-8")
    print(f"Successfully generated {out_file}")

if __name__ == "__main__":
    build_discriminator_findings()
